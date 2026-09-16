"""보안 미들웨어.

이전 구현의 문제:
- rate_limit_store 가 프로세스 메모리 defaultdict 라 키가 영구 누적(메모리 누수)됐고,
  워커를 늘리면 무력화됐다.
- get_client_ip 가 X-Forwarded-For 첫 값을 무조건 신뢰해 헤더 위조로 100% 우회됐다.
- XSS 정규식이 모든 POST body 전체에 걸려 정상 롤플레이 텍스트를 400 으로 막으면서,
  정작 JSON 유니코드 이스케이프(\\u003cscript)는 그대로 통과시켰다.

여기서는 IP 신뢰 경로를 명시하고, 카운터에 만료를 두며,
XSS 는 입력 차단이 아니라 응답 헤더(CSP/nosniff)와 출력 인코딩으로 다룬다.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core import cache
from core.config import IS_PROD, RATE_LIMIT_ENABLED, TRUSTED_PROXY

# path prefix -> (요청 수, 윈도우 초)
RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    "/auth/login": (5, 60),
    "/auth/register": (3, 60),
    "/chat": (30, 60),
    "/community": (60, 60),
    # LLM 을 태우는 경로는 반드시 제한한다 (기존에는 빠져 있어 비용 공격이 가능했다)
    "/characters/auto-complete": (10, 60),
    "/characters": (60, 60),
    "/tokens/ad-watch": (5, 60),
    "/party/rooms": (10, 60),
}

_buckets: dict[str, deque] = defaultdict(deque)
_lock = Lock()
_last_sweep = time.time()
_SWEEP_INTERVAL = 300


def client_ip(request: Request) -> str:
    """신뢰할 수 있는 프록시 뒤에 있을 때만 전달 헤더를 사용한다."""
    if TRUSTED_PROXY == "cloudflare":
        cf = request.headers.get("CF-Connecting-IP")
        if cf:
            return cf.strip()
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Cloudflare 가 붙이는 마지막 홉이 실제 클라이언트에 가장 가깝다
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _sweep_locked(now: float) -> None:
    global _last_sweep
    if now - _last_sweep < _SWEEP_INTERVAL:
        return
    _last_sweep = now
    for key in [k for k, q in _buckets.items() if not q or now - q[-1] > 3600]:
        _buckets.pop(key, None)


def is_rate_limited(key: str, limit: int, window: int) -> bool:
    # Redis 가 있으면 워커 전체가 같은 카운터를 공유한다
    shared = cache.incr_window(f"stellia:rl:{key}:{int(time.time()) // window}", window)
    if shared is not None:
        return shared > limit

    now = time.time()
    with _lock:
        _sweep_locked(now)
        bucket = _buckets[key]
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
        return False


def _match_rule(path: str) -> tuple[str, int, int] | None:
    best = None
    for route, (limit, window) in RATE_LIMIT_RULES.items():
        if path.startswith(route):
            # 더 구체적인 prefix 가 이긴다 (/characters/auto-complete > /characters)
            if best is None or len(route) > len(best[0]):
                best = (route, limit, window)
    return best


CSP = (
    "default-src 'self'; "
    "img-src 'self' data: blob:; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "object-src 'none'; "
    "base-uri 'self'"
)


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rule = _match_rule(request.url.path) if RATE_LIMIT_ENABLED else None
        if rule:
            route, limit, window = rule
            if is_rate_limited(f"{client_ip(request)}:{route}", limit, window):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "요청이 너무 많아요. 잠시 후 다시 시도해주세요."},
                    headers={"Retry-After": str(window)},
                )

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers.setdefault("Content-Security-Policy", CSP)
        if IS_PROD:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
