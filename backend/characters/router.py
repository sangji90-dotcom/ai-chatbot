from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from database import get_db
from auth.router import get_current_user, get_optional_user
import uuid
import shutil

router = APIRouter(prefix="/characters", tags=["characters"])

class CreateCharacterRequest(BaseModel):
    name: str
    description: str = ""
    age: int = 20
    personality: str
    speech_style: str
    likes: str = "없음"
    dislikes: str = "없음"
    job: str = "없음"
    first_message: str = ""
    situation: str = ""
    category: str = "기타"
    visibility: str = "public"
    image_url: str = ""

@router.get("")
async def get_characters(
        sort: str = "latest",
        current_user: dict = Depends(get_optional_user)):
    from prompt import characters

    result = [
        {
            "id": k,
            "name": v["name"],
            "custom": False,
            "description": v.get("description", ""),
            "category": v.get("category", ""),
            "first_message": v.get("first_message", ""),
            "situation": v.get("situation", ""),
            "image_url": v.get("image_url", ""),
            "chat_count": v.get("chat_count", 0)
        }
        for k, v in characters.items()
    ]

    conn = get_db()
    cursor = conn.cursor()

    order = {
        "latest": "created_at DESC",
        "popular": "chat_count DESC",
        "oldest": "created_at ASC"
    }.get(sort, "created_at DESC")

    if current_user:
        cursor.execute(f"""
            SELECT * FROM characters
            WHERE visibility = 'public' OR user_id = ?
            ORDER BY {order}
        """, (current_user["id"],))
    else:
        cursor.execute(f"""
            SELECT * FROM characters
            WHERE visibility = 'public'
            ORDER BY {order}
        """)

    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        result.append({
            "id": row["id"],
            "name": row["name"],
            "custom": True,
            "description": row["description"],
            "category": row["category"],
            "first_message": row["first_message"],
            "situation": row["situation"],
            "image_url": row["image_url"],
            "chat_count": row["chat_count"],
            "is_mine": current_user and row["user_id"] == current_user["id"]
        })

    return result

@router.post("")
async def create_character(
        request: CreateCharacterRequest,
        current_user: dict = Depends(get_current_user)):
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
        (id, user_id, name, description, prompt, first_message, situation, category, visibility, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id, current_user["id"], request.name, request.description,
        prompt, request.first_message, request.situation,
        request.category, request.visibility, request.image_url
    ))
    conn.commit()
    conn.close()

    return {"id": char_id, "name": request.name, "message": "캐릭터 생성 완료"}

@router.delete("/{char_id}")
async def delete_character(
        char_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM characters WHERE id = ?", (char_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 캐릭터만 삭제 가능합니다.")

    cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
    conn.commit()
    conn.close()
    return {"message": "캐릭터 삭제 완료"}

@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"../frontend/images/{filename}"

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"image_url": f"/images/{filename}"}