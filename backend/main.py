from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from database import init_db
from auth.router import router as auth_router
from characters.router import router as characters_router
from chat.router import router as chat_router
from users.router import router as users_router
import os

load_dotenv()

app = FastAPI(title="AI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("../frontend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# DB 초기화
init_db()

# 라우터 등록
app.include_router(auth_router)
app.include_router(characters_router)
app.include_router(chat_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "AI Chatbot API"}

@app.post("/upload/image")
async def upload_image_route():
    pass