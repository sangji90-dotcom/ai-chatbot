from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

chat_histories = {}

class ChatRequest(BaseModel):
    character_id: str
    message: str
    session_id: str

@app.get("/")
async def root():
    return {"message": "AI Chatbot API"}

@app.get("/characters")
async def get_characters():
    from prompt import characters
    return [
        {"id": k, "name": v["name"]}
        for k, v in characters.items()
    ]

@app.post("/chat")
async def chat(request: ChatRequest):
    from prompt import characters

    if request.character_id not in characters:
        return {"error": "캐릭터를 찾을 수 없습니다"}

    character = characters[request.character_id]
    session_key = f"{request.session_id}_{request.character_id}"

    if session_key not in chat_histories:
        chat_histories[session_key] = []

    history = chat_histories[session_key]

    # 대화 기록 + 새 메시지 합치기
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