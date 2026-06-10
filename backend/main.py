from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import shutil
import uuid
import sqlite3
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("../frontend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# SQLite 초기화
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            prompt TEXT NOT NULL,
            first_message TEXT DEFAULT '',
            situation TEXT DEFAULT '',
            category TEXT DEFAULT '기타',
            visibility TEXT DEFAULT 'public',
            image_url TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

chat_histories = {}

class ChatRequest(BaseModel):
    character_id: str
    message: str
    session_id: str

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

def get_db():
    conn = sqlite3.connect("chatbot.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {"message": "AI Chatbot API"}

@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        return {"error": "지원하지 않는 파일 형식입니다"}

    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"../frontend/images/{filename}"

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"image_url": f"/images/{filename}"}

@app.get("/characters")
async def get_characters():
    from prompt import characters

    # 기본 캐릭터
    result = [
        {
            "id": k,
            "name": v["name"],
            "custom": False,
            "description": v.get("description", ""),
            "category": v.get("category", ""),
            "first_message": v.get("first_message", ""),
            "situation": v.get("situation", ""),
            "image_url": v.get("image_url", "")
        }
        for k, v in characters.items()
    ]

    # DB에서 유저 생성 캐릭터 불러오기
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters ORDER BY created_at DESC")
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
            "image_url": row["image_url"]
        })

    return result

@app.post("/characters")
async def create_character(request: CreateCharacterRequest):
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
        INSERT INTO characters (id, name, description, prompt, first_message, situation, category, visibility, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        char_id,
        request.name,
        request.description,
        prompt,
        request.first_message,
        request.situation,
        request.category,
        request.visibility,
        request.image_url
    ))
    conn.commit()
    conn.close()

    return {"id": char_id, "name": request.name, "message": "캐릭터 생성 완료"}

@app.post("/chat")
async def chat(request: ChatRequest):
    from prompt import characters

    # 기본 캐릭터 + DB 캐릭터에서 찾기
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

    conn.close()

    if request.character_id not in all_characters:
        return {"error": "캐릭터를 찾을 수 없습니다"}

    character = all_characters[request.character_id]
    session_key = f"{request.session_id}_{request.character_id}"

    if session_key not in chat_histories:
        chat_histories[session_key] = []

    history = chat_histories[session_key]

    history.append({"role": "user", "content": request.message})

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

    return {
        "character": character["name"],
        "message": assistant_message
    }

@app.delete("/chat/{session_id}/{character_id}")
async def clear_chat(session_id: str, character_id: str):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "대화 기록 삭제 완료"}

@app.delete("/characters/{char_id}")
async def delete_character(char_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
    conn.commit()
    conn.close()
    return {"message": "캐릭터 삭제 완료"}