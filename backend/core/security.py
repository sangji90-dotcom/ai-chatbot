"""JWT 발급/검증 + 비밀번호 해싱.

기존 대비 변경점:
- SECRET fallback 제거 (core.config 에서 강제)
- decode_token() 에 expected_type 을 추가. access 자리에 refresh 토큰을 넣는
  우회(30일 토큰으로 전 API 호출)를 원천 차단한다.
- jti 부여로 개별 토큰 무효화 기반 마련
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from core.config import JWT_SECRET

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _encode(user_id: int, email: str, token_type: str, delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + delta,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def create_access_token(user_id: int, email: str) -> str:
    return _encode(user_id, email, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int, email: str) -> str:
    return _encode(user_id, email, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str | None = None) -> dict | None:
    """expected_type 을 넘기면 토큰 종류가 일치할 때만 payload 를 돌려준다."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if expected_type and payload.get("type") != expected_type:
        return None
    if "sub" not in payload:
        return None
    return payload
