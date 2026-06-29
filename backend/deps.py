from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from auth.jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    if user["suspended"]:
        raise HTTPException(status_code=403, detail="정지된 계정입니다.")

    return dict(user)

def get_optional_user(token: str = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return None
    if user["suspended"]:
        return None
    return dict(user)