import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

# core.config 를 가장 먼저 import 한다 — 필수 환경변수가 없으면 여기서 즉시 실패시킨다
from core.config import CORS_ORIGINS, FRONTEND_DIST, IS_PROD, UPLOAD_DIR
from core.logging_mw import RequestContextMiddleware
from core.middleware import SecurityMiddleware
from database import init_db

from achievements.router import init_achievements, router as achievements_router
from admin.router import router as admin_router
from auth.router import router as auth_router
from banners.router import router as banners_router
from characters.router import router as characters_router
from chat.router import router as chat_router
from community.router import router as community_router
from events.router import router as events_router
from follows.router import router as follows_router
from likes.router import router as likes_router
from notices.router import router as notices_router
from notifications.router import router as notifications_router
from party.router import router as party_router
from purchases.router import router as purchases_router
from reviews.router import router as reviews_router
from scheduler import start_scheduler
from suggestions.router import router as suggestions_router
from support.router import router as support_router
from terms.router import init_terms_db, router as terms_router
from tokens.router import router as tokens_router
from users.router import router as users_router

logging.basicConfig(
    level=logging.INFO if not IS_PROD else logging.WARNING,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB 초기화를 import 시점이 아니라 lifespan 으로 옮긴다
    # (import 부수효과로 DB 를 건드리면 테스트·마이그레이션에서 사고가 난다)
    init_db()
    init_achievements()
    init_terms_db()

    # 스케줄러는 프로세스마다 뜨면 만료 차감이 N중으로 걸린다.
    # 워커를 늘릴 때는 RUN_SCHEDULER=0 으로 두고 전용 프로세스 하나에서만 켤 것.
    if os.getenv("RUN_SCHEDULER", "1") == "1":
        start_scheduler()
    else:
        logger.info("scheduler disabled (RUN_SCHEDULER=0)")
    yield


app = FastAPI(
    title="Stellia API",
    description="AI 캐릭터 챗봇 서비스",
    version="1.1.0",
    lifespan=lifespan,
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None,
    openapi_url=None if IS_PROD else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestContextMiddleware)


# ── 예외 처리 ────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    # pydantic validator 의 한국어 메시지를 그대로 노출한다
    first = exc.errors()[0] if exc.errors() else {}
    msg = first.get("msg", "입력값이 올바르지 않아요.")
    return JSONResponse(status_code=422, content={"detail": msg.replace("Value error, ", "")})


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail},
                        headers=getattr(exc, "headers", None))


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    # 스택트레이스를 클라이언트로 흘리지 않는다
    rid = getattr(request.state, "request_id", "-")
    logger.exception("rid=%s unhandled error on %s %s", rid, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "일시적인 오류가 발생했어요.", "request_id": rid},
    )


@app.get("/health", include_in_schema=False)
def health():
    """프로세스만 살아 있고 DB 가 죽은 상태를 정상으로 보고하면 안 된다."""
    from core import cache
    from core.db import read_only

    checks = {"db": "ok", "cache": "redis" if cache.available() else "memory"}
    try:
        with read_only() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        logger.error("health check DB 실패: %s", exc)
        checks["db"] = "fail"
        return JSONResponse(status_code=503, content={"status": "degraded", **checks})
    return {"status": "ok", **checks}


# ── 라우터 ───────────────────────────────────────────────────
for r in (
    auth_router, characters_router, chat_router, users_router, party_router,
    likes_router, follows_router, banners_router, suggestions_router, tokens_router,
    achievements_router, support_router, admin_router, notifications_router,
    events_router, purchases_router, reviews_router, notices_router,
    community_router, terms_router,
):
    app.include_router(r)


# ── 정적 파일 ────────────────────────────────────────────────
# 업로드 이미지는 앱과 같은 오리진에서 서빙된다. 확장자를 서버가 판정하도록 바꿨지만
# (utils.read_image_with_ext), 운영에서는 Object Storage + 별도 도메인으로 분리할 것.
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(UPLOAD_DIR)), name="images")

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    logger.warning("frontend dist 없음: %s (npm run build 후 다시 기동)", FRONTEND_DIST)
