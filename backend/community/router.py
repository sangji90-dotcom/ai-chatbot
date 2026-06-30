from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from database import get_db
from deps import get_current_user, get_optional_user
from google import genai
import os, base64
from dotenv import load_dotenv
from utils import read_and_validate_image

load_dotenv()
router = APIRouter(prefix="/community", tags=["커뮤니티"])
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

GENRE_OPTIONS = ["fantasy", "modern", "sf", "horror", "romance", "other"]


# ── Gemini Vision: 장르 분류 + 설명 자동생성 ──────────────────
async def analyze_image_with_gemini(image_bytes: bytes, content: str) -> dict:
    try:
        image_b64 = base64.b64encode(image_bytes).decode()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
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
            config={"max_output_tokens": 300}
        )
        import json, re
        text = response.text.strip()
        text = re.sub(r'```json|```', '', text).strip()
        return json.loads(text)
    except:
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

    where = ["p.status = 'active'"]
    params = []

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

    # 캐릭터 태그 붙이기
    for post in posts:
        cursor.execute("""
            SELECT c.id, c.name, c.image_url FROM post_character_tags t
            JOIN characters c ON t.character_id = c.id
            WHERE t.post_id = ?
        """, (post["id"],))
        post["character_tags"] = [dict(r) for r in cursor.fetchall()]

        # 내가 좋아요 눌렀는지
        if current_user:
            cursor.execute("""
                SELECT 1 FROM community_likes WHERE post_id = ? AND user_id = ?
            """, (post["id"], current_user["id"]))
            post["is_liked"] = cursor.fetchone() is not None
        else:
            post["is_liked"] = False

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
    image_url = None
    genre = "other"
    ai_description = ""

    # 이미지 처리 + Gemini Vision 분석
    if image:
        image_bytes = await read_and_validate_image(image, max_size=10 * 1024 * 1024)

        # 저장
        upload_dir = "../frontend/images/community"
        os.makedirs(upload_dir, exist_ok=True)
        import uuid
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        image_url = f"/images/community/{filename}"

        # Gemini Vision 분석
        result = await analyze_image_with_gemini(image_bytes, content)
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
        for char_id in ids:
            # 캐릭터 존재 확인
            cursor.execute("SELECT user_id FROM characters WHERE id = ?", (char_id,))
            char = cursor.fetchone()
            if not char:
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
        cursor.execute("""
            INSERT INTO community_likes (post_id, user_id) VALUES (?, ?)
        """, (post_id, current_user["id"]))
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
    content: str

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
    title: Optional[str] = None
    content: Optional[str] = None

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