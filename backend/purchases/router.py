from fastapi import APIRouter, Depends, HTTPException
from deps import get_current_user
from database import get_db
from events.router import check_payment_streak
from datetime import datetime

router = APIRouter(prefix="/purchases", tags=["결제"])


# ── 구매 내역 조회 ─────────────────────────────────────────────
@router.get("/history")
def get_purchase_history(current_user=Depends(get_current_user)):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM purchases WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["id"],)
    ).fetchall()
    return [dict(r) for r in rows]


# ── 구매 요청 (PG사 연동 전 임시 - 관리자 수동 지급용) ──────────
@router.post("/manual")
def manual_purchase(body: dict, current_user=Depends(get_current_user)):
    """
    PG사 연동 전 임시 엔드포인트.
    실제 결제 연동 후 이 함수 내부만 교체하면 됨.
    """
    db = get_db()
    token_amount = body.get("token_amount", 0)

    if token_amount <= 0:
        raise HTTPException(400, "올바른 토큰 수량을 입력해주세요.")

    now = datetime.utcnow().isoformat()

    # 구매 내역 기록
    db.execute(
        "INSERT INTO purchases (user_id, amount, token_amount, payment_method, status) VALUES (?, ?, ?, ?, ?)",
        (current_user["id"], 0, token_amount, "manual", "completed")
    )

    # 금화 지급
    db.execute(
        "UPDATE users SET token_purchased = token_purchased + ? WHERE id = ?",
        (token_amount, current_user["id"])
    )
    db.execute(
        "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, ?, 'gold', '토큰 구매')",
        (current_user["id"], token_amount)
    )

    # 5일 연속 결제 streak 체크
    check_payment_streak(current_user["id"], token_amount, db)

    db.commit()
    return {"message": f"금화 {token_amount:,}개 지급 완료"}


# ── PG사 연동 후 여기에 webhook/callback 엔드포인트 추가 예정 ──
# @router.post("/webhook")
# def payment_webhook(body: dict): ...