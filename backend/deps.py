"""인증/인가 의존성.

변경점:
- access 토큰만 허용 (refresh 토큰으로 API 호출하던 우회 차단)
- require_admin / character_access 를 공통화. 각 라우터가 제각각 검사하거나
  아예 빠뜨리던(= /chat) 문제를 의존성 한 곳으로 모은다.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.db import read_only
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="유효하지 않은 토큰입니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _load_user(token: str | None):
    payload = decode_token(token, expected_type="access")
    if not payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None

    with read_only() as cur:
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cur.fetchone()

    if not user:
        return None
    return dict(user)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    user = _load_user(token)
    if not user:
        raise _UNAUTH
    if user.get("suspended"):
        raise HTTPException(status_code=403, detail="정지된 계정입니다.")
    return user


def get_optional_user(token: str | None = Depends(oauth2_scheme_optional)) -> dict | None:
    if not token:
        return None
    user = _load_user(token)
    if not user or user.get("suspended"):
        return None
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    return current_user


def require_adult(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_adult"):
        raise HTTPException(status_code=403, detail="성인 인증이 필요합니다.")
    return current_user


def assert_character_access(character_id: str, user: dict | None) -> dict:
    """캐릭터 접근 권한 단일 검사 지점.

    - 존재하지 않으면 404
    - private 인데 소유자가 아니면 403
    - 성인 캐릭터인데 미인증이면 403
    """
    with read_only() as cur:
        cur.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")

    char = dict(row)
    if char.get("visibility") == "private":
        if not user or char.get("user_id") != user.get("id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    if char.get("is_adult"):
        if not user or not user.get("is_adult"):
            raise HTTPException(status_code=403, detail="성인 인증이 필요합니다.")
    return char


def assert_owner(character_id: str, user: dict) -> dict:
    with read_only() as cur:
        cur.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    char = dict(row)
    if char.get("user_id") != user.get("id"):
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    return char
