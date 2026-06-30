import os
import re
import time
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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
from notifications.router import router as notifications_router
from events.router import router as events_router
from purchases.router import router as purchases_router
from reviews.router import router as reviews_router
from notices.router import router as notices_router
from community.router import router as community_router
from terms.router import router as terms_router, init_terms_db

load_dotenv()

# ── Rate Limiting ─────────────────────────────────────────────
rate_limit_store = defaultdict(list)

RATE_LIMIT_RULES = {
    "/auth/login":        (5,  60),
    "/auth/register":     (3,  60),
    "/chat":              (30, 60),
    "/community":         (60, 60),
}

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def is_rate_limited(key: str, limit: int, window: int) -> bool:
    now = time.time()
    rate_limit_store[key] = [t for t in rate_limit_store[key] if now - t < window]
    if len(rate_limit_store[key]) >= limit:
        return True
    rate_limit_store[key].append(now)
    return False

# ── XSS 필터 ─────────────────────────────────────────────────
XSS_PATTERN = re.compile(
    r'<script.*?>.*?</script>|javascript:|on\w+\s*=|<iframe|<object|<embed|<link|<meta',
    re.IGNORECASE | re.DOTALL
)

def contains_xss(value: str) -> bool:
    return bool(XSS_PATTERN.search(value))

async def check_xss_in_body(request: Request) -> bool:
    try:
        body = await request.body()
        if body:
            text = body.decode("utf-8", errors="ignore")
            return contains_xss(text)
    except:
        pass
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="AI 챗봇 API",
    description="AI 캐릭터 챗봇 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url=None,
    openapi_tags=[
        {"name": "인증",     "description": "회원가입 / 로그인 / 내 정보"},
        {"name": "캐릭터",   "description": "캐릭터 생성 / 조회 / 삭제 / 검색"},
        {"name": "대화",     "description": "AI와 대화 / 대화 기록 / 요약 / 이어하기"},
        {"name": "유저",     "description": "내 캐릭터 / 최근 대화 / 노트 / 페르소나 / 메모리북 / 설정"},
        {"name": "파티챗",   "description": "스토리 / 방 생성 / 실시간 파티 채팅"},
        {"name": "좋아요",   "description": "캐릭터 좋아요 / 좋아요 목록"},
        {"name": "팔로우",   "description": "창작자 팔로우 / 새 캐릭터 알림"},
        {"name": "배너",     "description": "메인 배너 조회 / 관리"},
        {"name": "건의사항", "description": "서비스 건의사항 제출"},
        {"name": "토큰",     "description": "토큰 조회 / 출석 / 광고 시청 / 내역"},
        {"name": "업적",     "description": "업적 목록 / 달성 현황 / 토큰 보상"},
        {"name": "알림",     "description": "알림 목록 / 읽음 처리 / 삭제"},
        {"name": "이벤트",   "description": "친구 초대 / 출석 streak / 연속 결제 보상"},
        {"name": "결제",     "description": "구매 내역 / 토큰 구매"},
        {"name": "커뮤니티", "description": "게시글 / 댓글 / 좋아요 / 캐릭터 태그"},
        {"name": "약관",     "description": "이용약관 / 개인정보처리방침"},
    ]
)

# ── CORS ─────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "https://suburb-marrow-radial.ngrok-free.dev",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Rate Limit + XSS 미들웨어 ────────────────────────────────
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    ip = get_client_ip(request)
    path = request.url.path

    # Rate Limiting
    for route, (limit, window) in RATE_LIMIT_RULES.items():
        if path.startswith(route):
            key = f"{ip}:{route}"
            if is_rate_limited(key, limit, window):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "요청이 너무 많아요. 잠시 후 다시 시도해주세요."}
                )
            break

    # XSS 필터 — body를 읽지 않고 raw bytes만 캐싱 후 재주입
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if body:
            text = body.decode("utf-8", errors="ignore")
            if contains_xss(text):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "허용되지 않는 문자가 포함되어 있어요."}
                )
        # body를 다시 읽을 수 있도록 재주입
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


# ── Static ───────────────────────────────────────────────────
os.makedirs("../frontend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="../frontend/images"), name="images")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# ── DB 초기화 ────────────────────────────────────────────────
init_db()
init_achievements()
init_terms_db()

# ── 라우터 등록 ──────────────────────────────────────────────
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
app.include_router(notifications_router)
app.include_router(events_router)
app.include_router(purchases_router)
app.include_router(reviews_router)
app.include_router(notices_router)
app.include_router(community_router)
app.include_router(terms_router)

# ── 프론트엔드 static serve ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "../stellia-frontend/dist"), html=True), name="frontend")