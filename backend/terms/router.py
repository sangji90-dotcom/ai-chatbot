from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/terms", tags=["약관"])

# ── DB 테이블 초기화 (main.py init_db 대신 여기서 관리) ──────
def init_terms_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT UNIQUE NOT NULL,  -- 'terms' | 'privacy'
            content TEXT NOT NULL,
            version TEXT DEFAULT '1.0',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 기본 데이터 없으면 빈 값으로 초기화
    cursor.execute("""
        INSERT OR IGNORE INTO terms (type, content, version)
        VALUES ('terms', '이용약관 내용을 입력해주세요.', '1.0')
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO terms (type, content, version)
        VALUES ('privacy', '개인정보처리방침 내용을 입력해주세요.', '1.0')
    """)
    conn.commit()
    conn.close()


# ── 약관 조회 ─────────────────────────────────────────────────
@router.get("/{type}", summary="약관 조회")
async def get_terms(type: str):
    if type not in ["terms", "privacy"]:
        raise HTTPException(status_code=400, detail="type은 terms 또는 privacy만 가능합니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM terms WHERE type = ?", (type,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="약관을 찾을 수 없습니다.")
    return dict(row)


# ── 약관 수정 (관리자만) ──────────────────────────────────────
class TermsUpdateRequest(BaseModel):
    content: str
    version: Optional[str] = None

@router.put("/{type}", summary="약관 수정 (관리자)")
async def update_terms(
    type: str,
    request: TermsUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 수정 가능합니다.")
    if type not in ["terms", "privacy"]:
        raise HTTPException(status_code=400, detail="type은 terms 또는 privacy만 가능합니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE terms SET content = ?, version = COALESCE(?, version),
        updated_at = CURRENT_TIMESTAMP WHERE type = ?
    """, (request.content, request.version, type))
    conn.commit()
    conn.close()
    return {"message": "약관 수정 완료"}