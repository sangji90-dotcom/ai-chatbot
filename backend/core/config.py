"""중앙 설정. 필수값은 fallback 없이 강제한다 (시크릿 무단 기본값 금지)."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ENV = os.getenv("ENV", "development").lower()
IS_PROD = ENV == "production"


def _required(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        sys.stderr.write(
            f"[FATAL] 환경변수 {key} 가 비어 있습니다. backend/.env 를 확인하세요 "
            f"(backend/.env.example 참고).\n"
        )
        raise RuntimeError(f"missing required env: {key}")
    return value


JWT_SECRET = _required("JWT_SECRET")
if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET 은 32자 이상이어야 합니다. openssl rand -hex 32")

GEMINI_API_KEY = _required("GEMINI_API_KEY")

# DB 경로는 항상 절대경로로 고정한다 (실행 디렉터리에 따라 다른 DB가 열리는 사고 방지)
_db_env = os.getenv("DB_PATH", "").strip()
DB_PATH = str(Path(_db_env).resolve()) if _db_env else str(BASE_DIR / "chatbot.db")

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"

# none | cloudflare — 신뢰할 수 있는 프록시가 아니면 XFF 헤더를 믿지 않는다
TRUSTED_PROXY = os.getenv("TRUSTED_PROXY", "none").lower()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR.parent / "frontend" / "images"))).resolve()
FRONTEND_DIST = BASE_DIR.parent / "stellia-frontend" / "dist"

# 토큰 경제
CHAT_DEDUCT = 50
# 재생성 비용. LLM 을 한 번 더 호출하므로 기본은 대화와 동일하게 둔다.
# CBT 에서는 0 으로 두는 것을 고려할 것 — 재생성이 유료면 유저는 재생성 대신
# 이탈을 택하고, 그러면 10턴 도달률이 떨어져 기억 품질 검증 자체가 불가능해진다.
REGENERATE_COST = int(os.getenv("REGENERATE_COST", str(CHAT_DEDUCT)))
SIGNUP_TOKEN = 3000
ATTENDANCE_TOKEN = 1000
AD_TOKEN = 500
AD_DAILY_LIMIT = 2
EVENT_EXPIRE_DAYS = 21

# 채팅 세션 캐시
SESSION_CACHE_MAX = 500
SESSION_CACHE_TTL_SEC = 2 * 60 * 60

MIN_CHARACTER_AGE = 19

# 파티 방 생성 도배 방지 쿨다운 (초)
PARTY_ROOM_COOLDOWN_SEC = int(os.getenv("PARTY_ROOM_COOLDOWN_SEC", "10"))

# ── 기억(메모리) 동작 ────────────────────────────────────────
# CBT 에서는 기억 품질 자체가 검증 대상이라 유료 게이팅을 연다.
# 유료화 시점에 이 값만 0 으로 돌리면 메모리 패스 보유자 전용으로 되돌아간다.
MEMORY_FOR_ALL = os.getenv("MEMORY_FOR_ALL", "1") == "1"

# 몇 턴마다 기억을 추출할지
MEMORY_EXTRACT_EVERY = int(os.getenv("MEMORY_EXTRACT_EVERY", "10"))
# 패스 없는 유저가 주입받을 수 있는 기억 개수 (패스 보유자는 memory_chunk_limit)
MEMORY_FREE_CHUNKS = int(os.getenv("MEMORY_FREE_CHUNKS", "20"))
# 한 번 추출에서 최대 몇 개까지 받을지
MEMORY_MAX_PER_EXTRACT = 3

# 자동 요약 임계값. 요약은 기억을 '압축'하는 장치라 값이 낮을수록 손실이 크다.
AUTO_SUMMARY_THRESHOLD = int(os.getenv("AUTO_SUMMARY_THRESHOLD", "100"))
RECENT_TURNS_KEPT = int(os.getenv("RECENT_TURNS_KEPT", "40"))
