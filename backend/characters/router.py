import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from deps import get_current_user, get_optional_user
from notifications.router import send_notification

router = APIRouter(prefix="/characters", tags=["캐릭터"])


class CreateCharacterRequest(BaseModel):
    name: str
    age: int
    job: str
    personality: str
    likes: str
    dislikes: str
    speech_style: str
    description: str = ""
    first_message: str = ""
    situation: str = ""
    visibility: str = "public"
    is_adult: int = 0
    image_url: str = ""
    tags: List[str] = []


class UpdateCharacterRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    job: Optional[str] = None
    personality: Optional[str] = None
    likes: Optional[str] = None
    dislikes: Optional[str] = None
    speech_style: Optional[str] = None
    description: Optional[str] = None
    first_message: Optional[str] = None
    situation: Optional[str] = None
    visibility: Optional[str] = None
    is_adult: Optional[int] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class ReportRequest(BaseModel):
    reason: str


@router.post("", summary="캐릭터 생성")
async def create_character(
        request: CreateCharacterRequest,
        current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    char_id = f"custom_{request.name}_{uuid.uuid4().hex[:8]}"

    prompt = f"""
너는 {request.name}라는 캐릭터야.

기본 정보:
- 이름: {request.name}
- 나이: {request.age}세
- 직업: {request.job}

성격 및 외모:
{request.personality}

좋아하는 것: {request.likes}
싫어하는 것: {request.dislikes}

말투:
{request.speech_style}

{"시작 상황: " + request.situation if request.situation else ""}

절대 규칙:
- AI라고 절대 말하지 않음
- 캐릭터를 절대 벗어나지 않음
"""

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO characters
        (id, user_id, name, description, prompt, first_message, situation, visibility, is_adult, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id, current_user["id"], request.name, request.description,
        prompt, request.first_message, request.situation,
        request.visibility, request.is_adult, request.image_url
    ))

    for tag in request.tags:
        cursor.execute("INSERT INTO character_tags (character_id, tag) VALUES (?, ?)",
                       (char_id, tag))

    conn.commit()

    cursor.execute("SELECT COUNT(*) as cnt FROM characters WHERE user_id = ?",
                   (current_user["id"],))
    count = cursor.fetchone()["cnt"]
    conn.close()

    conn2 = get_db()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT follower_id FROM follows WHERE following_id = ?",
                    (current_user["id"],))
    followers = cursor2.fetchall()
    conn2.close()

    for follower in followers:
        send_notification(
            follower["follower_id"],
            "new_character",
            "팔로우한 창작자의 신작!",
            f"{current_user['username']}님이 새 캐릭터 '{request.name}'을 만들었어요!",
            f"/characters/{char_id}"
        )

    if count == 1: check_and_grant(current_user["id"], "first_character")
    if count == 5: check_and_grant(current_user["id"], "character_5")
    if count == 10: check_and_grant(current_user["id"], "character_10")

    return {"id": char_id, "name": request.name, "message": "캐릭터 생성 완료"}


@router.get("/ranking", summary="인기 캐릭터 랭킹")
async def get_ranking(
        limit: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        {adult_filter}
        GROUP BY c.id
        ORDER BY c.like_count DESC, c.chat_count DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("/new", summary="신규 캐릭터")
async def get_new_characters(
        limit: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        {adult_filter}
        GROUP BY c.id
        ORDER BY c.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("/category/{category}", summary="카테고리별 캐릭터")
async def get_characters_by_category(
        category: str,
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        AND c.id IN (SELECT character_id FROM character_tags WHERE tag = ?)
        {adult_filter}
        GROUP BY c.id
        ORDER BY c.chat_count DESC
        LIMIT ? OFFSET ?
    """, (category, size, (page - 1) * size))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("", summary="캐릭터 목록 조회")
async def get_characters(
        tag: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    if tag:
        cursor.execute(f"""
            SELECT c.*, GROUP_CONCAT(ct.tag) as tags
            FROM characters c
            LEFT JOIN character_tags ct ON c.id = ct.character_id
            WHERE c.visibility = 'public'
            AND c.id IN (SELECT character_id FROM character_tags WHERE tag = ?)
            {adult_filter}
            GROUP BY c.id
            ORDER BY c.chat_count DESC, c.created_at DESC
            LIMIT ? OFFSET ?
        """, (tag, size, (page - 1) * size))
    else:
        cursor.execute(f"""
            SELECT c.*, GROUP_CONCAT(ct.tag) as tags
            FROM characters c
            LEFT JOIN character_tags ct ON c.id = ct.character_id
            WHERE c.visibility = 'public'
            {adult_filter}
            GROUP BY c.id
            ORDER BY c.chat_count DESC, c.created_at DESC
            LIMIT ? OFFSET ?
        """, (size, (page - 1) * size))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("/me", summary="내 캐릭터 목록")
async def get_my_characters(
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.user_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("/search", summary="캐릭터 검색")
async def search_characters(
        q: str,
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        AND (c.name LIKE ? OR c.description LIKE ?)
        {adult_filter}
        GROUP BY c.id
        ORDER BY c.chat_count DESC
        LIMIT ? OFFSET ?
    """, (f"%{q}%", f"%{q}%", size, (page - 1) * size))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.get("/user/{user_id}", summary="특정 유저의 캐릭터 목록")
async def get_characters_by_user(
        user_id: int,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"
    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.user_id = ?
        AND c.visibility = 'public'
        {adult_filter}
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_character(row) for row in rows]


@router.post("/{character_id}/image", summary="캐릭터 이미지 업로드")
async def upload_character_image(
        character_id: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    if not char:
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if char["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        conn.close()
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        conn.close()
        raise HTTPException(status_code=400, detail="파일 크기는 5MB 이하여야 합니다.")
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = "../frontend/images/characters"
    os.makedirs(save_dir, exist_ok=True)
    with open(f"{save_dir}/{filename}", "wb") as f:
        f.write(contents)
    image_url = f"/images/characters/{filename}"
    cursor.execute("UPDATE characters SET image_url = ? WHERE id = ?", (image_url, character_id))
    conn.commit()
    conn.close()
    return {"image_url": image_url, "message": "이미지 업로드 완료"}


@router.post("/{character_id}/report", summary="캐릭터 신고")
async def report_character(
        character_id: str,
        request: ReportRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM characters WHERE id = ?", (character_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    try:
        cursor.execute("""
            INSERT INTO character_reports (user_id, character_id, reason)
            VALUES (?, ?, ?)
        """, (current_user["id"], character_id, request.reason))
        conn.commit()
        conn.close()
        return {"message": "신고 완료"}
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 신고한 캐릭터입니다.")


@router.get("/{character_id}", summary="캐릭터 상세 조회")
async def get_character(
        character_id: str,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.id = ?
        GROUP BY c.id
    """, (character_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if row["visibility"] == "private":
        if not current_user or row["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    if row["is_adult"]:
        if not current_user or not current_user.get("is_adult"):
            raise HTTPException(status_code=403, detail="성인 인증이 필요합니다.")
    return _format_character(row)


@router.put("/{character_id}", summary="캐릭터 수정")
async def update_character(
        character_id: str,
        request: UpdateCharacterRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    if not char:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if char["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")
    fields = []
    params = []
    if request.name is not None:
        fields.append("name = ?"); params.append(request.name)
    if request.description is not None:
        fields.append("description = ?"); params.append(request.description)
    if request.first_message is not None:
        fields.append("first_message = ?"); params.append(request.first_message)
    if request.situation is not None:
        fields.append("situation = ?"); params.append(request.situation)
    if request.visibility is not None:
        fields.append("visibility = ?"); params.append(request.visibility)
    if request.is_adult is not None:
        fields.append("is_adult = ?"); params.append(request.is_adult)
    if request.image_url is not None:
        fields.append("image_url = ?"); params.append(request.image_url)
    if any([request.name, request.age, request.job, request.personality,
            request.likes, request.dislikes, request.speech_style]):
        name = request.name or char["name"]
        age = request.age or 0
        job = request.job or ""
        personality = request.personality or ""
        likes = request.likes or ""
        dislikes = request.dislikes or ""
        speech_style = request.speech_style or ""
        situation = request.situation or char["situation"]
        new_prompt = f"""
너는 {name}라는 캐릭터야.

기본 정보:
- 이름: {name}
- 나이: {age}세
- 직업: {job}

성격 및 외모:
{personality}

좋아하는 것: {likes}
싫어하는 것: {dislikes}

말투:
{speech_style}

{"시작 상황: " + situation if situation else ""}

절대 규칙:
- AI라고 절대 말하지 않음
- 캐릭터를 절대 벗어나지 않음
"""
        fields.append("prompt = ?"); params.append(new_prompt)
    if fields:
        params.append(character_id)
        cursor.execute(f"UPDATE characters SET {', '.join(fields)} WHERE id = ?", params)
    if request.tags is not None:
        cursor.execute("DELETE FROM character_tags WHERE character_id = ?", (character_id,))
        for tag in request.tags:
            cursor.execute("INSERT INTO character_tags (character_id, tag) VALUES (?, ?)",
                           (character_id, tag))
    conn.commit()
    conn.close()
    return {"message": "캐릭터 수정 완료"}


@router.delete("/{character_id}", summary="캐릭터 삭제")
async def delete_character(
        character_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    if not char:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if char["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    cursor.execute("DELETE FROM character_tags WHERE character_id = ?", (character_id,))
    cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
    conn.commit()
    conn.close()
    return {"message": "캐릭터 삭제 완료"}


def _format_character(row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "description": row["description"],
        "first_message": row["first_message"],
        "situation": row["situation"],
        "visibility": row["visibility"],
        "is_adult": bool(row["is_adult"]),
        "image_url": row["image_url"],
        "chat_count": row["chat_count"],
        "like_count": row["like_count"],
        "tags": row["tags"].split(",") if row["tags"] else [],
        "created_at": row["created_at"],
    }