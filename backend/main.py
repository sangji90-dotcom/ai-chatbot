import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from database import init_db
from auth.router import router as auth_router
from characters.router import router as characters_router
from chat.router import router as chat_router
from users.router import router as users_router
from party.router import router as party_router
from likes.router import router as likes_router
from follows.router import router as follows_router
from banners.router import router as banners_router
from suggestions.router import router as suggestions_router
from tokens.router import router as tokens_router
from achievements.router import router as achievements_router, init_achievements
from scheduler import start_scheduler
from support.router import router as support_router
from admin.router import router as admin_router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title="AI 챗봇 API",
    description="AI 캐릭터 챗봇 서비스",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "인증", "description": "회원가입 / 로그인 / 내 정보"},
        {"name": "캐릭터", "description": "캐릭터 생성 / 조회 / 삭제 / 검색"},
        {"name": "대화", "description": "AI와 대화 / 대화 기록 / 요약 / 이어하기"},
        {"name": "유저", "description": "내 캐릭터 / 최근 대화 / 노트 / 페르소나 / 메모리북 / 설정"},
        {"name": "파티챗", "description": "스토리 / 방 생성 / 실시간 파티 채팅"},
        {"name": "좋아요", "description": "캐릭터 좋아요 / 좋아요 목록"},
        {"name": "팔로우", "description": "창작자 팔로우 / 새 캐릭터 알림"},
        {"name": "배너", "description": "메인 배너 조회 / 관리"},
        {"name": "건의사항", "description": "서비스 건의사항 제출"},
        {"name": "토큰", "description": "토큰 조회 / 출석 / 광고 시청 / 내역"},
        {"name": "업적", "description": "업적 목록 / 달성 현황 / 토큰 보상"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("../frontend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

init_db()
init_achievements()

app.include_router(auth_router)
app.include_router(characters_router)
app.include_router(chat_router)
app.include_router(users_router)
app.include_router(party_router)
app.include_router(likes_router)
app.include_router(follows_router)
app.include_router(banners_router)
app.include_router(suggestions_router)
app.include_router(tokens_router)
app.include_router(achievements_router)
app.include_router(support_router)
app.include_router(admin_router)

@app.get("/", tags=["기본"])
async def root():
    return {"message": "AI 챗봇 API"}