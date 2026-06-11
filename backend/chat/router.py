from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db
from auth.router import get_optional_user
from google import genai
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/chat", tags=["chat"])
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat_histories = {}

class ChatRequest(BaseModel):
    character_id: str
    message: str
    session_id: str

@router.post("")
async def chat(
        request: ChatRequest,
        current_user: dict = Depends(get_optional_user)):
    from prompt import characters

    all_characters = dict(characters)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (request.character_id,))
    row = cursor.fetchone()

    if row:
        all_characters[row["id"]] = {
            "name": row["name"],
            "prompt": row["prompt"]
        }
        # 대화 수 증가
        cursor.execute(
            "UPDATE characters SET chat_count = chat_count + 1 WHERE id = ?",
            (request.character_id,)
        )
        conn.commit()

    conn.close()

    if request.character_id not in all_characters:
        return {"error": "캐릭터를 찾을 수 없습니다"}

    character = all_characters[request.character_id]
    session_key = f"{request.session_id}_{request.character_id}"

    if session_key not in chat_histories:
        chat_histories[session_key] = []

    history = chat_histories[session_key]
    history.append({"role": "user", "content": request.message})

    # DB에 대화 저장
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, character_id, user_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.session_id, request.character_id,
        current_user["id"] if current_user else None,
        "user", request.message
    ))

    contents = []
    for msg in history[-30:]:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "system_instruction": character["prompt"],
            "max_output_tokens": 1000,
        }
    )

    assistant_message = response.text
    history.append({"role": "assistant", "content": assistant_message})
    chat_histories[session_key] = history

    cursor.execute("""
        INSERT INTO chat_history (session_id, character_id, user_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.session_id, request.character_id,
        current_user["id"] if current_user else None,
        "assistant", assistant_message
    ))
    conn.commit()
    conn.close()

    return {"character": character["name"], "message": assistant_message}

@router.get("/history/{character_id}")
async def get_chat_history(
        character_id: str,
        current_user: dict = Depends(get_optional_user)):
    if not current_user:
        return []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, created_at FROM chat_history
        WHERE character_id = ? AND user_id = ?
        ORDER BY created_at ASC
    """, (character_id, current_user["id"]))
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@router.delete("/{session_id}/{character_id}")
async def clear_chat(session_id: str, character_id: str):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "대화 기록 삭제 완료"}