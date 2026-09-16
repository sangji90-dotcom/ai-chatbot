"""요청 추적용 미들웨어.

장애가 나면 '어느 요청이 터졌는지'를 로그에서 이어 붙일 수 있어야 한다.
요청마다 ID 를 발급해 로그와 응답 헤더(X-Request-ID)에 함께 남긴다.
"""
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("access")

# 로그에 남기면 안 되는 경로 (본문에 비밀번호가 들어간다)
_SENSITIVE = ("/auth/login", "/auth/register", "/users/me/password")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.perf_counter() - started) * 1000
            logger.exception(
                "rid=%s %s %s -> EXC %.1fms", request_id, request.method,
                request.url.path, elapsed,
            )
            raise

        elapsed = (time.perf_counter() - started) * 1000
        path = request.url.path
        level = logging.WARNING if response.status_code >= 500 else logging.INFO
        if response.status_code >= 400 or elapsed > 1000 or path not in _SENSITIVE:
            logger.log(
                level, "rid=%s %s %s -> %s %.1fms",
                request_id, request.method, path, response.status_code, elapsed,
            )
        response.headers["X-Request-ID"] = request_id
        return response
