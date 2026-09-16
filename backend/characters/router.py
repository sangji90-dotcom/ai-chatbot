import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List
from database import get_db
from deps import get_current_user, get_optional_user, assert_owner
from notifications.router import send_notification
from utils import read_image_with_ext
from pydantic import field_validator
from core.config import MIN_CHARACTER_AGE, UPLOAD_DIR
from chat import llm

router = APIRouter(prefix="/characters", tags=["캐릭터"])


class CreateCharacterRequest(BaseModel):
    name: str
    age: int

    @field_validator("age")
    @classmethod
    def _adult_only(cls, v: int) -> int:
        # 프롬프트의 "절대 규칙" 문구는 강제력이 없다. 서버에서 막는다.
        if v < MIN_CHARACTER_AGE:
            raise ValueError(f"캐릭터 나이는 {MIN_CHARACTER_AGE}세 이상만 등록할 수 있어요.")
        if v > 200:
            raise ValueError("나이가 올바르지 않아요.")
        return v
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
    party_enabled: int = 0


class UpdateCharacterRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None

    @field_validator("age")
    @classmethod
    def _adult_only(cls, v):
        if v is None:
            return v
        if v < MIN_CHARACTER_AGE:
            raise ValueError(f"캐릭터 나이는 {MIN_CHARACTER_AGE}세 이상만 등록할 수 있어요.")
        if v > 200:
            raise ValueError("나이가 올바르지 않아요.")
        return v
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
    party_enabled: Optional[int] = None


class ReportRequest(BaseModel):
    reason: str


class AutoCompleteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    description: str = Field(default="", max_length=1000)
    job: str = Field(default="", max_length=100)
    age: int = 20

    @field_validator("age")
    @classmethod
    def _adult_only(cls, v: int) -> int:
        if v < MIN_CHARACTER_AGE:
            raise ValueError(f"{MIN_CHARACTER_AGE}세 이상만 생성할 수 있어요.")
        return v


@router.post("/auto-complete", summary="캐릭터 자동완성")
async def auto_complete_character(
        request: AutoCompleteRequest,
        current_user: dict = Depends(get_current_user)):

    prompt = f"""
캐릭터 정보:
- 이름: {request.name}
- 나이: {request.age}세
- 직업: {request.job}
- 소개: {request.description}

위 정보를 바탕으로 아래 항목을 JSON으로 생성해줘. 반드시 JSON만 출력하고 다른 텍스트는 없어야 해.

절대 규칙:
- 미성년자(18세 미만) 캐릭터의 성적/로맨틱 묘사 절대 금지
- 아동 성적 콘텐츠(로리, 쇼타 등) 절대 생성 금지
- 혐오, 차별, 폭력적 표현 금지
- 특정 실존 인물 사칭 금지

{{
  "personality": "성격 설명 (3~5문장)",
  "speech_style": "말투 설명 (2~3문장)",
  "likes": "좋아하는 것 (쉼표로 구분)",
  "dislikes": "싫어하는 것 (쉼표로 구분)",
  "first_message": "첫 대사 (1~2문장)",
  "situation": "시작 상황 설명 (2~3문장)"
}}
"""

    response = await llm.generate(
        [{"role": "user", "parts": [{"text": prompt}]}],
        system_instruction="반드시 JSON만 출력한다.",
        max_output_tokens=2000,
    )

    import json, re
    text = llm.text_of(response).strip()
    text = re.sub(r'```json\s*|\s*```', '', text).strip()

    try:
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"[AUTO-COMPLETE ERROR] {e} | 응답: {text}")
        raise HTTPException(status_code=500, detail="AI 자동완성 실패")


@router.post("", summary="캐릭터 생성")
async def create_character(
        request: CreateCharacterRequest,
        current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    char_id = f"custom_{uuid.uuid4().hex}"  # 이름을 PK/URL 에 넣지 않는다 (한글·특수문자 사고 방지)

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
- 미성년자(18세 미만) 캐릭터와의 성적/로맨틱/신체적 묘사 절대 금지
- 아동 성적 콘텐츠(로리, 쇼타 포함) 절대 생성 금지
- 위 요청이 들어오면 단호하게 거절하고 대화 주제를 바꿀 것
"""

    if request.visibility not in ("public", "private"):
        raise HTTPException(status_code=400, detail="visibility 는 public 또는 private 만 가능합니다.")
    if len(request.tags) > 10:
        raise HTTPException(status_code=400, detail="태그는 최대 10개까지 등록할 수 있어요.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO characters
        (id, user_id, name, description, prompt, first_message, situation, visibility, is_adult,
         image_url, party_enabled, likes, dislikes, age, job, personality, speech_style)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id, current_user["id"], request.name, request.description,
        prompt, request.first_message, request.situation,
        request.visibility, request.is_adult, request.image_url, request.party_enabled,
        request.likes, request.dislikes,
        # 구조화 필드를 컬럼으로도 남긴다 — 수정 시 프롬프트에서 역파싱할 필요가 없어진다
        request.age, request.job, request.personality, request.speech_style
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
        sort: str = "popular",
        period: str = "all",
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"

    sort_map = {
        "popular": "c.like_count DESC, c.chat_count DESC",
        "latest": "c.created_at DESC",
        "oldest": "c.created_at ASC",
        "chat": "c.chat_count DESC",
        "view": "c.view_count DESC",
    }
    order = sort_map.get(sort, "c.like_count DESC, c.chat_count DESC")

    period_filter = ""
    if period == "weekly":
        period_filter = "AND c.created_at >= datetime('now', '-7 days')"
    elif period == "monthly":
        period_filter = "AND c.created_at >= datetime('now', '-30 days')"

    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        {adult_filter}
        {period_filter}
        GROUP BY c.id
        ORDER BY {order}
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
        sort: str = "popular",
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"

    sort_map = {
        "popular": "c.like_count DESC, c.chat_count DESC",
        "latest": "c.created_at DESC",
        "oldest": "c.created_at ASC",
        "chat": "c.chat_count DESC",
        "view": "c.view_count DESC",
    }
    order = sort_map.get(sort, "c.like_count DESC, c.chat_count DESC")

    if tag:
        cursor.execute(f"""
            SELECT c.*, GROUP_CONCAT(ct.tag) as tags
            FROM characters c
            LEFT JOIN character_tags ct ON c.id = ct.character_id
            WHERE c.visibility = 'public'
            AND c.id IN (SELECT character_id FROM character_tags WHERE tag = ?)
            {adult_filter}
            GROUP BY c.id
            ORDER BY {order}
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
            ORDER BY {order}
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
        sort: str = "popular",
        tag: Optional[str] = None,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    is_adult = current_user.get("is_adult", 0) if current_user else 0
    adult_filter = "" if is_adult else "AND c.is_adult = 0"

    sort_map = {
        "popular": "c.like_count DESC, c.chat_count DESC",
        "latest": "c.created_at DESC",
        "oldest": "c.created_at ASC",
        "chat": "c.chat_count DESC",
        "view": "c.view_count DESC",
    }
    order = sort_map.get(sort, "c.like_count DESC, c.chat_count DESC")

    tag_filter = ""
    params = [f"%{q}%", f"%{q}%"]
    if tag:
        tag_filter = "AND c.id IN (SELECT character_id FROM character_tags WHERE tag = ?)"
        params.append(tag)

    params += [size, (page - 1) * size]

    cursor.execute(f"""
        SELECT c.*, GROUP_CONCAT(ct.tag) as tags
        FROM characters c
        LEFT JOIN character_tags ct ON c.id = ct.character_id
        WHERE c.visibility = 'public'
        AND (c.name LIKE ? OR c.description LIKE ?)
        {tag_filter}
        {adult_filter}
        GROUP BY c.id
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """, params)
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


# upload_character_image 수정
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

    contents, ext = await read_image_with_ext(file, max_size=5 * 1024 * 1024)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = str(UPLOAD_DIR / "characters")
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
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if row["visibility"] == "private":
        if not current_user or row["user_id"] != current_user["id"]:
            conn.close()
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    if row["is_adult"]:
        if not current_user or not current_user.get("is_adult"):
            conn.close()
            raise HTTPException(status_code=403, detail="성인 인증이 필요합니다.")

    if not current_user or current_user["id"] != row["user_id"]:
        cursor.execute("UPDATE characters SET view_count = view_count + 1 WHERE id = ?",
                       (character_id,))
        conn.commit()

    conn.close()
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
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if char["user_id"] != current_user["id"]:
        conn.close()
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
    if request.party_enabled is not None:
        fields.append("party_enabled = ?"); params.append(request.party_enabled)
    if request.likes is not None:
        fields.append("likes = ?"); params.append(request.likes)
    if request.dislikes is not None:
        fields.append("dislikes = ?"); params.append(request.dislikes)
    if any([request.name, request.age, request.job, request.personality,
            request.likes, request.dislikes, request.speech_style]):
        # 보내지 않은 필드는 기존 값을 유지한다.
        # 예전에는 0 / "" 으로 떨어져서 저장 한 번에 나이가 0세가 되고 직업·성격이 지워졌다.
        def _keep(new, column, default):
            if new not in (None, ""):
                return new
            try:
                stored = char[column]
            except (IndexError, KeyError):
                stored = None
            return stored if stored not in (None, "") else default

        name = request.name or char["name"]
        age = _keep(request.age, "age", 20)
        job = _keep(request.job, "job", "")
        personality = _keep(request.personality, "personality", "")
        speech_style = _keep(request.speech_style, "speech_style", "")
        likes = _keep(request.likes, "likes", "")
        dislikes = _keep(request.dislikes, "dislikes", "")
        situation = request.situation or char["situation"]

        if int(age) < MIN_CHARACTER_AGE:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"캐릭터 나이는 {MIN_CHARACTER_AGE}세 이상만 등록할 수 있어요.",
            )

        # 재생성한 프롬프트와 컬럼을 함께 갱신해 둘이 어긋나지 않게 한다
        for col, val in (("age", age), ("job", job),
                         ("personality", personality), ("speech_style", speech_style)):
            fields.append(f"{col} = ?")
            params.append(val)
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
- 미성년자(18세 미만) 캐릭터와의 성적/로맨틱/신체적 묘사 절대 금지
- 아동 성적 콘텐츠(로리, 쇼타 포함) 절대 생성 금지
- 위 요청이 들어오면 단호하게 거절하고 대화 주제를 바꿀 것
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
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if char["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    # FK 에 ON DELETE CASCADE 가 없어 고아 레코드가 남던 문제 — 명시적으로 정리
    for stmt in (
        "DELETE FROM character_tags WHERE character_id = ?",
        "DELETE FROM character_images WHERE character_id = ?",
        "DELETE FROM character_backgrounds WHERE character_id = ?",
        "DELETE FROM character_likes WHERE character_id = ?",
        "DELETE FROM character_bookmarks WHERE character_id = ?",
        "DELETE FROM character_reviews WHERE character_id = ?",
        "DELETE FROM character_reports WHERE character_id = ?",
        "DELETE FROM chat_history WHERE character_id = ?",
        "DELETE FROM user_notes WHERE character_id = ?",
        "DELETE FROM user_personas WHERE character_id = ?",
        "DELETE FROM memory_book WHERE character_id = ?",
    ):
        cursor.execute(stmt, (character_id,))
    cursor.execute("DELETE FROM characters WHERE id = ?", (character_id,))
    conn.commit()
    conn.close()
    return {"message": "캐릭터 삭제 완료"}


EMOTIONS = ["neutral", "happy", "sad", "angry", "shy", "surprised", "love", "embarrassed", "crying", "serious"]
SITUATIONS = ["default", "indoor", "outdoor", "night", "cafe", "forest", "rain", "sunny", "fantasy", "dramatic"]


@router.post("/{character_id}/emotions/{emotion}", summary="감정별 이미지 업로드")
async def upload_emotion_image(
        character_id: str,
        emotion: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)):
    if emotion not in EMOTIONS:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 감정 태그예요. 가능: {EMOTIONS}")
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

    contents, ext = await read_image_with_ext(file, max_size=5 * 1024 * 1024)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = str(UPLOAD_DIR / "emotions")
    os.makedirs(save_dir, exist_ok=True)
    with open(f"{save_dir}/{filename}", "wb") as f:
        f.write(contents)
    image_url = f"/images/emotions/{filename}"
    cursor.execute("SELECT id FROM character_images WHERE character_id = ? AND emotion = ?",
                   (character_id, emotion))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE character_images SET image_url = ? WHERE id = ?",
                       (image_url, existing["id"]))
    else:
        cursor.execute("INSERT INTO character_images (character_id, emotion, image_url) VALUES (?, ?, ?)",
                       (character_id, emotion, image_url))
    conn.commit()
    conn.close()
    return {"emotion": emotion, "image_url": image_url, "message": "감정 이미지 업로드 완료"}


@router.get("/{character_id}/emotions", summary="감정별 이미지 목록")
async def get_emotion_images(character_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT emotion, image_url FROM character_images WHERE character_id = ?",
                   (character_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row["emotion"]: row["image_url"] for row in rows}


@router.post("/{character_id}/backgrounds/{situation}", summary="상황별 배경 업로드")
async def upload_background_image(
        character_id: str,
        situation: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)):
    if situation not in SITUATIONS:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 상황 태그예요. 가능: {SITUATIONS}")
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

    contents, ext = await read_image_with_ext(file, max_size=10 * 1024 * 1024)

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = str(UPLOAD_DIR / "backgrounds")
    os.makedirs(save_dir, exist_ok=True)
    with open(f"{save_dir}/{filename}", "wb") as f:
        f.write(contents)
    image_url = f"/images/backgrounds/{filename}"
    cursor.execute("SELECT id FROM character_backgrounds WHERE character_id = ? AND situation = ?",
                   (character_id, situation))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE character_backgrounds SET image_url = ? WHERE id = ?",
                       (image_url, existing["id"]))
    else:
        cursor.execute("INSERT INTO character_backgrounds (character_id, situation, image_url) VALUES (?, ?, ?)",
                       (character_id, situation, image_url))
    conn.commit()
    conn.close()
    return {"situation": situation, "image_url": image_url, "message": "배경 이미지 업로드 완료"}


@router.get("/{character_id}/backgrounds", summary="상황별 배경 목록")
async def get_background_images(character_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT situation, image_url FROM character_backgrounds WHERE character_id = ?",
                   (character_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row["situation"]: row["image_url"] for row in rows}


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
        "view_count": row["view_count"] if "view_count" in row.keys() else 0,
        "party_enabled": bool(row["party_enabled"]) if "party_enabled" in row.keys() else False,
        "tags": row["tags"].split(",") if row["tags"] else [],
        "created_at": row["created_at"],
        "likes": row["likes"] if "likes" in row.keys() else "",
        "dislikes": row["dislikes"] if "dislikes" in row.keys() else "",
    }