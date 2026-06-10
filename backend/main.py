from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import shutil
import uuid

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 이미지 저장 폴더
os.makedirs("../frontend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

chat_histories = {}
custom_characters = {}

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
    result += [
        {
            "id": k,
            "name": v["name"],
            "custom": True,
            "description": v.get("description", ""),
            "category": v.get("category", ""),
            "first_message": v.get("first_message", ""),
            "situation": v.get("situation", ""),
            "image_url": v.get("image_url", "")
        }
        for k, v in custom_characters.items()
    ]
    return result

@app.post("/characters")
async def create_character(request: CreateCharacterRequest):
    char_id = f"custom_{request.name}_{len(custom_characters)}"

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

    custom_characters[char_id] = {
        "name": request.name,
        "description": request.description,
        "prompt": prompt,
        "first_message": request.first_message,
        "situation": request.situation,
        "category": request.category,
        "visibility": request.visibility,
        "image_url": request.image_url
    }

    return {"id": char_id, "name": request.name, "message": "캐릭터 생성 완료"}

@app.post("/characters/{char_id}/generate-image")
async def generate_image(char_id: str):
    # TODO: DALL-E 연동 (나중에)
    return {"message": "AI 이미지 생성은 준비 중입니다"}

@app.post("/chat")
async def chat(request: ChatRequest):
    from prompt import characters

    all_characters = {**characters, **custom_characters}

    if request.character_id not in all_characters:
        return {"error": "캐릭터를 찾을 수 없습니다"}

    character = all_characters[request.character_id]
    session_key = f"{request.session_id}_{request.character_id}"

    if session_key not in chat_histories:
        chat_histories[session_key] = []

    history = chat_histories[session_key]

    contents = []
    for msg in history[-30:]:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })
    contents.append({
        "role": "user",
        "parts": [{"text": request.message}]
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

    history.append({"role": "user", "content": request.message})
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