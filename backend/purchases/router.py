"""결제 라우터.

이전 구현의 `POST /purchases/manual` 은 요청 body 의 token_amount 를 그대로 믿고
금화를 지급했다. 로그인 계정 하나로 무한 충전이 가능했으므로 관리자 전용으로 옮긴다.

PG 연동 시 해야 할 일 (이 파일 하단 webhook 자리):
  1) PG 서명/해시 검증
  2) 서버가 보관한 주문의 금액과 PG 통지 금액 대조 (클라이언트 값은 신뢰하지 않음)
  3) merchant_uid 를 idempotency_key 로 사용해 중복 지급 차단
  4) 지급은 반드시 core.token_service.grant() 경유
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core import token_service as ts
from core.db import read_only, transaction
from deps import get_current_user, require_admin

router = APIRouter(prefix="/purchases", tags=["결제"])


class ManualGrantRequest(BaseModel):
    user_id: int
    token_amount: int = Field(gt=0, le=1_000_000)
    reason: str = "관리자 수동 지급"


@router.get("/history", summary="내 구매 내역")
def get_purchase_history(current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        cur.execute(
            "SELECT * FROM purchases WHERE user_id = ? ORDER BY created_at DESC",
            (current_user["id"],),
        )
        return [dict(r) for r in cur.fetchall()]


@router.post("/manual", summary="[관리자] 금화 수동 지급")
def manual_grant(body: ManualGrantRequest, admin: dict = Depends(require_admin)):
    from events.router import check_payment_streak

    with transaction() as cur:
        cur.execute("SELECT id FROM users WHERE id = ?", (body.user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        cur.execute(
            "INSERT INTO purchases (user_id, amount, token_amount, payment_method, status) "
            "VALUES (?, 0, ?, 'manual', 'completed')",
            (body.user_id, body.token_amount),
        )
        purchase_id = cur.lastrowid

        ts.grant(cur, body.user_id, body.token_amount, ts.GOLD, body.reason,
                 idempotency_key=f"manual:{purchase_id}")

        try:
            check_payment_streak(body.user_id, body.token_amount, cur)
        except TypeError:
            # 레거시 시그니처(conn 기대) 호환 — streak 실패가 지급을 막지 않도록
            pass

    return {"message": f"금화 {body.token_amount:,}개 지급 완료", "purchase_id": purchase_id}


# @router.post("/webhook")
# def payment_webhook(...): ...   # 위 주석의 1~4번을 모두 구현한 뒤 열 것
