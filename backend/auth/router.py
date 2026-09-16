from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from database import get_db
from auth.jwt import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from datetime import datetime, timedelta
from deps import get_current_user, get_optional_user
from fastapi import APIRouter, HTTPException, Depends, Request

router = APIRouter(prefix="/auth", tags=["인증"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _strength(cls, v: str) -> str:
        # 길이만 있는 비밀번호는 bcrypt 로도 못 막는다
        if v.isdigit() or v.isalpha():
            raise ValueError("비밀번호는 영문과 숫자를 함께 포함해야 해요.")
        return v

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str

class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_tokens(user_id: int, email: str, username: str, cursor, conn) -> TokenResponse:
    access = create_access_token(user_id, email)
    refresh = create_refresh_token(user_id, email)
    expires_at = datetime.utcnow() + timedelta(days=30)

    # 같은 유저의 세션을 전부 끊으면 웹 로그인 시 앱이 튕긴다.
    # 만료된 것과 상한 초과분만 정리해 멀티 디바이스를 허용한다.
    cursor.execute(
        "DELETE FROM refresh_tokens WHERE user_id = ? AND expires_at < datetime('now')", (user_id,)
    )
    cursor.execute(
        """
        DELETE FROM refresh_tokens
         WHERE user_id = ?
           AND id NOT IN (
               SELECT id FROM refresh_tokens WHERE user_id = ?
               ORDER BY created_at DESC LIMIT 4
           )
        """,
        (user_id, user_id),
    )
    cursor.execute(
        "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, refresh, expires_at)
    )
    conn.commit()
    return TokenResponse(access_token=access, refresh_token=refresh, username=username)


@router.post("/register", summary="회원가입")
async def register(request: RegisterRequest, req: Request):
    from achievements.router import check_and_grant

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    
    client_ip = req.client.host
    cursor.execute("SELECT count FROM ip_registrations WHERE ip = ?", (client_ip,))
    ip_row = cursor.fetchone()
    if ip_row:
        cursor.execute(
            "UPDATE ip_registrations SET count = count + 1, last_registered_at = ? WHERE ip = ?",
            (datetime.now().isoformat(), client_ip)
        )
    else:
        cursor.execute(
            "INSERT INTO ip_registrations (ip, count) VALUES (?, 1)",
            (client_ip,)
        )
    conn.commit()

    hashed = hash_password(request.password)
    cursor.execute(
        "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
        (request.email, request.username, hashed)
    )
    conn.commit()
    user_id = cursor.lastrowid

    expires_at = datetime.now() + timedelta(days=21)
    cursor.execute("UPDATE users SET token_balance = 3000, token_event = 3000 WHERE id = ?", (user_id,))
    cursor.execute("""
        INSERT INTO token_history (user_id, amount, token_type, reason, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, 3000, "event", "회원가입 기본 지급", expires_at))
    conn.commit()
    check_and_grant(user_id, "first_signup")

    result = _issue_tokens(user_id, request.email, request.username, cursor, conn)
    conn.close()
    return result


@router.post("/login", summary="로그인")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form.username,))
    user = cursor.fetchone()

    if not user or not verify_password(form.password, user["password"]):
        conn.close()
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")

    if user["suspended"]:
        conn.close()
        raise HTTPException(status_code=403, detail="정지된 계정입니다. 고객센터에 문의해주세요.")

    result = _issue_tokens(user["id"], user["email"], user["username"], cursor, conn)
    conn.close()
    return result


@router.post("/refresh", summary="토큰 갱신")
async def refresh_token(request: RefreshRequest):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM refresh_tokens WHERE token = ? AND user_id = ?",
        (request.refresh_token, int(payload["sub"]))
    )
    stored = cursor.fetchone()

    if not stored:
        conn.close()
        raise HTTPException(status_code=401, detail="만료되거나 존재하지 않는 토큰입니다.")

    if datetime.utcnow() > datetime.fromisoformat(stored["expires_at"]):
        cursor.execute("DELETE FROM refresh_tokens WHERE token = ?", (request.refresh_token,))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=401, detail="리프레시 토큰이 만료되었습니다. 다시 로그인해주세요.")

    cursor.execute("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),))
    user = cursor.fetchone()

    result = _issue_tokens(user["id"], user["email"], user["username"], cursor, conn)
    conn.close()
    return result


@router.post("/logout", summary="로그아웃")
async def logout(request: RefreshRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM refresh_tokens WHERE token = ?", (request.refresh_token,))
    conn.commit()
    conn.close()
    return {"message": "로그아웃 완료"}