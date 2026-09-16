from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from database import get_db
from core.db import read_only, transaction
from deps import get_current_user, get_optional_user
import os, base64
from utils import EXT_BY_MIME, read_image_with_ext
from core.config import UPLOAD_DIR
from chat import llm

router = APIRouter(prefix="/community", tags=["커뮤니티"])

GENRE_OPTIONS = ["fantasy", "modern", "sf", "horror", "romance", "other"]
POST_TYPES = ["general", "party", "review", "question"]
MAX_CONTENT_LEN = 5000
MAX_COMMENT_LEN = 1000


# ── Gemini Vision: 장르 분류 + 설명 자동생성 ──────────────────
async def analyze_image_with_gemini(image_bytes: bytes, content: str, mime: str = "image/jpeg") -> dict:
    """동기 generate_content 를 async 안에서 부르면 이벤트 루프가 멈춘다.
    mime_type 도 실제 판정값을 쓴다 (기존엔 png/gif 도 image/jpeg 로 보냈음)."""
    try:
        image_b64 = base64.b64encode(image_bytes).decode()
        response = await llm.generate(
            [{
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": image_b64
                        }
                    },
                    {
                        "text": f"""
이 이미지와 게시글 내용을 분석해줘.

게시글 내용: {content}

반드시 아래 JSON 형식으로만 답해줘. 설명 없이 JSON만:
{{
  "genre": "fantasy|modern|sf|horror|romance|other 중 하나",
  "description": "이미지와 내용을 기반으로 한 게시글 설명 초안 (2~3문장)"
}}
"""
                    }
                ]
            }],
            system_instruction="반드시 JSON 만 출력한다.",
            max_output_tokens=300,
        )
        import json, re
        text = llm.text_of(response).strip()
        text = re.sub(r'```json|```', '', text).strip()
        data = json.loads(text)
        genre = data.get("genre", "other")
        return {
            "genre": genre if genre in GENRE_OPTIONS else "other",
            "description": str(data.get("description", ""))[:500],
        }
    except Exception:
        return {"genre": "other", "description": ""}


# ── 게시글 목록 ──────────────────────────────────────────────
@router.get("", summary="커뮤니티 피드")
async def get_posts(
    post_type: Optional[str] = None,
    genre: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_optional_user)
):
    conn = get_db()
    cursor = conn.cursor()

    limit = min(max(1, limit), 50)
    page = max(1, page)

    where = ["p.status = 'active'"]
    params = []

    # is_adult 컬럼이 있는데 목록에서 전혀 쓰지 않아 성인 게시글이 그대로 노출됐다
    if not (current_user and current_user.get("is_adult")):
        where.append("p.is_adult = 0")

    if post_type:
        where.append("p.post_type = ?")
        params.append(post_type)
    if genre:
        where.append("p.genre = ?")
        params.append(genre)

    where_sql = " AND ".join(where)
    offset = (page - 1) * limit

    cursor.execute(f"""
        SELECT p.*, u.username, u.profile_image_url,
               u.equipped_prefix, u.equipped_suffix,
               (SELECT COUNT(*) FROM community_likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM community_comments WHERE post_id = p.id AND status = 'active') as comment_count
        FROM community_posts p
        JOIN users u ON p.user_id = u.id
        WHERE {where_sql}
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    posts = [dict(r) for r in cursor.fetchall()]
    post_ids = [p["id"] for p in posts]

    # 기존에는 게시글마다 쿼리를 2번씩 돌려 20개 조회에 41쿼리가 나갔다 (N+1)
    tags_by_post: dict[int, list] = {pid: [] for pid in post_ids}
    liked: set[int] = set()
    if post_ids:
        marks = ",".join("?" * len(post_ids))
        cursor.execute(f"""
            SELECT t.post_id, c.id, c.name, c.image_url
            FROM post_character_tags t
            JOIN characters c ON t.character_id = c.id
            WHERE t.post_id IN ({marks})
        """, post_ids)
        for r in cursor.fetchall():
            tags_by_post[r["post_id"]].append(
                {"id": r["id"], "name": r["name"], "image_url": r["image_url"]}
            )
        if current_user:
            cursor.execute(
                f"SELECT post_id FROM community_likes WHERE user_id = ? AND post_id IN ({marks})",
                [current_user["id"], *post_ids],
            )
            liked = {r["post_id"] for r in cursor.fetchall()}

    for post in posts:
        post["character_tags"] = tags_by_post.get(post["id"], [])
        post["is_liked"] = post["id"] in liked

    conn.close()
    return posts


# ── 게시글 작성 ──────────────────────────────────────────────
@router.post("", summary="게시글 작성")
async def create_post(
    content: str = Form(...),
    post_type: str = Form("general"),
    title: Optional[str] = Form(None),
    character_ids: Optional[str] = Form(None),  # 콤마 구분 "char1,char2"
    party_character_id: Optional[str] = Form(None),
    party_max: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    if len(content) > MAX_CONTENT_LEN:
        raise HTTPException(status_code=400, detail=f"본문은 {MAX_CONTENT_LEN}자 이하로 작성해주세요.")
    if post_type not in POST_TYPES:
        post_type = "general"
    if party_max is not None and not (2 <= party_max <= 10):
        raise HTTPException(status_code=400, detail="파티 인원은 2~10명 사이여야 해요.")

    image_url = None
    genre = "other"
    ai_description = ""

    # 이미지 처리 + Gemini Vision 분석
    if image:
        # 확장자는 magic bytes 판정 결과로 결정한다 (filename 신뢰 금지)
        image_bytes, ext = await read_image_with_ext(image, max_size=10 * 1024 * 1024)

        # 저장
        upload_dir = str(UPLOAD_DIR / "community")
        os.makedirs(upload_dir, exist_ok=True)
        import uuid
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        image_url = f"/images/community/{filename}"

        # Gemini Vision 분석
        mime = next((m for m, e in EXT_BY_MIME.items() if e == ext), "image/jpeg")
        result = await analyze_image_with_gemini(image_bytes, content, mime)
        genre = result.get("genre", "other")
        ai_description = result.get("description", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO community_posts
        (user_id, title, content, post_type, genre, ai_description,
         image_url, party_character_id, party_max)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        current_user["id"], title, content, post_type,
        genre, ai_description, image_url,
        party_character_id, party_max
    ))
    post_id = cursor.lastrowid

    # 캐릭터 태그 처리
    if character_ids:
        ids = [c.strip() for c in character_ids.split(",") if c.strip()]
        for char_id in ids[:10]:
            # 존재 + 공개 여부 확인.
            # 기존엔 존재만 확인해서 남의 private 캐릭터를 태그해 이름/이미지를 노출시킬 수 있었다
            cursor.execute(
                "SELECT user_id, visibility, is_adult FROM characters WHERE id = ?", (char_id,)
            )
            char = cursor.fetchone()
            if not char:
                continue
            if char["visibility"] != "public" and char["user_id"] != current_user["id"]:
                continue
            if char["is_adult"] and not current_user.get("is_adult"):
                continue

            cursor.execute("""
                INSERT INTO post_character_tags (post_id, character_id)
                VALUES (?, ?)
            """, (post_id, char_id))

            # 원작자 알림 (본인 캐릭터 태그 제외)
            if char["user_id"] and char["user_id"] != current_user["id"]:
                cursor.execute("""
                    INSERT INTO notifications (user_id, type, title, message, link)
                    VALUES (?, 'community_tag', '내 캐릭터가 태그됐어요', ?, ?)
                """, (
                    char["user_id"],
                    f"{current_user['username']}님이 게시글에 내 캐릭터를 태그했어요",
                    f"/community/{post_id}"
                ))

    conn.commit()
    conn.close()

    return {
        "id": post_id,
        "genre": genre,
        "ai_description": ai_description,
        "image_url": image_url,
        "message": "게시글 작성 완료"
    }


# ── 게시글 상세 ──────────────────────────────────────────────
@router.get("/{post_id}", summary="게시글 상세")
async def get_post(post_id: int, current_user: dict = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE community_posts SET view_count = view_count + 1 WHERE id = ?
    """, (post_id,))

    cursor.execute("""
        SELECT p.*, u.username, u.profile_image_url,
               u.equipped_prefix, u.equipped_suffix,
               (SELECT COUNT(*) FROM community_likes WHERE post_id = p.id) as like_count,
               (SELECT COUNT(*) FROM community_comments WHERE post_id = p.id AND status = 'active') as comment_count
        FROM community_posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ? AND p.status = 'active'
    """, (post_id,))

    post = cursor.fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    post = dict(post)

    cursor.execute("""
        SELECT c.id, c.name, c.image_url FROM post_character_tags t
        JOIN characters c ON t.character_id = c.id
        WHERE t.post_id = ?
    """, (post_id,))
    post["character_tags"] = [dict(r) for r in cursor.fetchall()]

    if current_user:
        cursor.execute("""
            SELECT 1 FROM community_likes WHERE post_id = ? AND user_id = ?
        """, (post_id, current_user["id"]))
        post["is_liked"] = cursor.fetchone() is not None
    else:
        post["is_liked"] = False

    # 댓글
    cursor.execute("""
        SELECT c.*, u.username, u.profile_image_url
        FROM community_comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ? AND c.status = 'active'
        ORDER BY c.created_at ASC
    """, (post_id,))
    post["comments"] = [dict(r) for r in cursor.fetchall()]

    conn.commit()
    conn.close()
    return post


# ── 좋아요 토글 ──────────────────────────────────────────────
@router.post("/{post_id}/like", summary="좋아요 토글")
async def toggle_like(post_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM community_likes WHERE post_id = ? AND user_id = ?
    """, (post_id, current_user["id"]))

    if cursor.fetchone():
        cursor.execute("""
            DELETE FROM community_likes WHERE post_id = ? AND user_id = ?
        """, (post_id, current_user["id"]))
        liked = False
    else:
        try:
            cursor.execute("""
                INSERT INTO community_likes (post_id, user_id) VALUES (?, ?)
            """, (post_id, current_user["id"]))
        except sqlite3.IntegrityError:
            pass  # 더블클릭 등으로 동시에 들어온 경우 — 이미 눌린 상태로 취급
        liked = True

    cursor.execute("""
        SELECT COUNT(*) as cnt FROM community_likes WHERE post_id = ?
    """, (post_id,))
    like_count = cursor.fetchone()["cnt"]

    conn.commit()
    conn.close()
    return {"liked": liked, "like_count": like_count}


# ── 댓글 작성 ────────────────────────────────────────────────
class CommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=MAX_COMMENT_LEN)

@router.post("/{post_id}/comments", summary="댓글 작성")
async def create_comment(
    post_id: int,
    request: CommentRequest,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id FROM community_posts WHERE id = ? AND status = 'active'
    """, (post_id,))
    post = cursor.fetchone()
    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    cursor.execute("""
        INSERT INTO community_comments (post_id, user_id, content)
        VALUES (?, ?, ?)
    """, (post_id, current_user["id"], request.content))

    # 게시글 작성자 알림 (본인 댓글 제외)
    if post["user_id"] != current_user["id"]:
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, link)
            VALUES (?, 'community_comment', '게시글에 댓글이 달렸어요', ?, ?)
        """, (
            post["user_id"],
            f"{current_user['username']}님이 댓글을 달았어요",
            f"/community/{post_id}"
        ))

    conn.commit()
    conn.close()
    return {"message": "댓글 작성 완료"}

class UpdatePostRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = Field(default=None, max_length=MAX_CONTENT_LEN)

@router.put("/{post_id}", summary="게시글 수정")
async def update_post(
    post_id: int,
    request: UpdatePostRequest,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM community_posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    if post["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

    fields = []
    params = []
    if request.title is not None:
        fields.append("title = ?")
        params.append(request.title)
    if request.content is not None:
        fields.append("content = ?")
        params.append(request.content)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(post_id)
        cursor.execute(f"UPDATE community_posts SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return {"message": "게시글 수정 완료"}

# ── 게시글 삭제 ──────────────────────────────────────────────
@router.delete("/{post_id}", summary="게시글 삭제")
async def delete_post(post_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id FROM community_posts WHERE id = ?
    """, (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

    if post["user_id"] != current_user["id"] and not current_user.get("is_admin"):
        conn.close()
        raise HTTPException(status_code=403, detail="권한 없음")

    cursor.execute("""
        UPDATE community_posts SET status = 'deleted' WHERE id = ?
    """, (post_id,))
    conn.commit()
    conn.close()
    return {"message": "게시글 삭제 완료"}

# ── 댓글 수정 / 삭제 ─────────────────────────────────────────
# 기존에는 댓글 작성 API 만 있고 수정·삭제가 없었다.
class UpdateCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=MAX_COMMENT_LEN)


@router.put("/comments/{comment_id}", summary="댓글 수정")
def update_comment(
    comment_id: int,
    request: UpdateCommentRequest,
    current_user: dict = Depends(get_current_user),
):
    with transaction() as cur:
        cur.execute(
            "UPDATE community_comments SET content = ? "
            " WHERE id = ? AND user_id = ? AND status = 'active'",
            (request.content, comment_id, current_user["id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
    return {"message": "댓글 수정 완료"}


@router.delete("/comments/{comment_id}", summary="댓글 삭제")
def delete_comment(comment_id: int, current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute("SELECT user_id FROM community_comments WHERE id = ?", (comment_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
        if row["user_id"] != current_user["id"] and not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="권한 없음")
        cur.execute(
            "UPDATE community_comments SET status = 'deleted' WHERE id = ?", (comment_id,)
        )
    return {"message": "댓글 삭제 완료"}
