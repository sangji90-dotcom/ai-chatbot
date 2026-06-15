from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from database import get_db
from auth.jwt import hash_password, verify_password, create_access_token, decode_token
from datetime import datetime, timedelta
from deps import get_current_user, get_optional_user
# from achievements.router import check_and_grant  ← 삭제

router = APIRouter(prefix="/auth", tags=["인증"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

@router.post("/register", summary="회원가입")
async def register(request: RegisterRequest):
    from achievements.router import check_and_grant  # ← 함수 내부로 이동

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

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
    conn.close()

    token = create_access_token(user_id, request.email)
    return TokenResponse(access_token=token, username=request.username)

@router.post("/login", summary="로그인")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form.username,))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 틀렸습니다.")

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(access_token=token, username=user["username"])

