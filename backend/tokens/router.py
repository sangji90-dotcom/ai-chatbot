from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from core import token_service as ts
from core.config import AD_DAILY_LIMIT, AD_TOKEN, ATTENDANCE_TOKEN, CHAT_DEDUCT, EVENT_EXPIRE_DAYS
from core.db import read_only, transaction
from deps import get_current_user, require_admin

router = APIRouter(
    prefix="/tokens",
    tags=["토큰"],
    responses={404: {"description": "찾을 수 없습니다"}},
)

SIGNUP_TOKEN = 3000
MEMORY_PASS_30DAY_COINS = 24900
MEMORY_PASS_CASH_PRICE = 9900
MEMORY_CHUNK_MAX = 100

TOKEN_PACKAGES = [
    {"id": 1, "price": 1900, "token_amount": 2000, "label": "2,000토큰"},
    {"id": 2, "price": 3800, "token_amount": 4200, "label": "4,200토큰 (+200 보너스)"},
    {"id": 3, "price": 9500, "token_amount": 11000, "label": "11,000토큰 (+1,000 보너스)"},
    {"id": 4, "price": 19000, "token_amount": 23000, "label": "23,000토큰 (+3,000 보너스)"},
]


# ── 하위 호환 API (다른 모듈이 import 중) ────────────────────────────────
def add_token(user_id: int, amount: int, token_type: str, reason: str,
              expires_at=None, idempotency_key: str | None = None) -> bool:
    return ts.grant_standalone(user_id, amount, token_type, reason, expires_at, idempotency_key)


def deduct_token(user_id: int, amount: int, reason: str) -> int:
    """잔액 부족이면 402. 알림은 차감 트랜잭션 밖에서 처리한다."""
    from notifications.router import send_notification

    try:
        remaining = ts.deduct_standalone(user_id, amount, reason)
    except ts.InsufficientTokens:
        send_notification(
            user_id, "token_empty", "토큰이 부족합니다",
            "토큰을 충전하고 대화를 계속해보세요!", "/tokens/packages",
        )
        raise

    if remaining <= 100:
        send_notification(
            user_id, "token_low", "토큰이 거의 소진됐어요",
            f"잔여 토큰: {remaining}개. 지금 충전하면 대화가 끊기지 않아요!", "/tokens/packages",
        )
    return remaining


# ── 조회 ────────────────────────────────────────────────────────────────
@router.get("/packages", summary="토큰 패키지 목록")
async def get_packages():
    return TOKEN_PACKAGES


@router.get("/me", summary="내 토큰 조회")
def get_my_tokens(current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        return ts.balance_of(cur, current_user["id"])


@router.get("/me/history", summary="토큰 내역")
def get_token_history(
    page: int = 1,
    size: int = 20,
    token_type: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    page = max(1, page)
    size = min(max(1, size), 100)

    where = "WHERE user_id = ?"
    params: list = [current_user["id"]]
    if token_type:
        where += " AND token_type = ?"
        params.append(token_type)

    with read_only() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM token_history {where}", params)
        total = cur.fetchone()["total"]
        cur.execute(
            f"SELECT * FROM token_history {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [size, (page - 1) * size],
        )
        items = [dict(r) for r in cur.fetchall()]

    return {"total": total, "page": page, "size": size, "items": items}


# ── 출석 / 광고 ─────────────────────────────────────────────────────────
@router.post("/attendance", summary="출석 체크")
def attendance_check(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    with transaction() as cur:
        cur.execute(
            "SELECT last_attendance_date, attendance_streak FROM users WHERE id = ?", (uid,)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        new_streak = (user["attendance_streak"] or 0) + 1 if user["last_attendance_date"] == yesterday else 1

        # 날짜 조건을 UPDATE 에 포함시켜 동시 요청의 중복 출석을 막는다
        cur.execute(
            """
            UPDATE users
               SET last_attendance_date = ?,
                   attendance_streak = ?,
                   streak_reward_claimed_at = CASE WHEN ? < 7 THEN NULL
                                                   ELSE streak_reward_claimed_at END
             WHERE id = ?
               AND (last_attendance_date IS NULL OR last_attendance_date != ?)
            """,
            (today, new_streak, new_streak, uid, today),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=400, detail="오늘 이미 출석했습니다.")

        expires_at = ts.silver_expiry(EVENT_EXPIRE_DAYS)
        ts.grant(cur, uid, ATTENDANCE_TOKEN, ts.SILVER, "출석 체크", expires_at,
                 idempotency_key=f"attendance:{uid}:{today}")

    # 출석 업적은 정의만 있고 지급 훅이 없어 영원히 받을 수 없었다.
    # (check_and_grant 는 자체 트랜잭션을 열므로 위 블록 밖에서 호출한다)
    from achievements.router import check_and_grant
    for threshold, code in ((1, "attendance_1"), (7, "attendance_7"),
                            (30, "attendance_30"), (100, "attendance_100")):
        if new_streak >= threshold:
            check_and_grant(uid, code)

    return {
        "message": f"출석 완료! {ATTENDANCE_TOKEN}토큰 지급 ({EVENT_EXPIRE_DAYS}일 유효)",
        "attendance_streak": new_streak,
        "expires_at": expires_at.strftime("%Y-%m-%d"),
    }


@router.post("/ad-watch", summary="광고 시청")
def watch_ad(current_user: dict = Depends(get_current_user)):
    # NOTE: 실제 광고 SDK 연동 시 서버 사이드 검증(SSV) 콜백으로 교체할 것.
    #       현재는 클라이언트 호출만으로 지급되므로 일일 한도가 유일한 방어선이다.
    uid = current_user["id"]
    today = str(date.today())

    with transaction() as cur:
        cur.execute("SELECT ad_watched_today, last_ad_date FROM users WHERE id = ?", (uid,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        watched = user["ad_watched_today"] if user["last_ad_date"] == today else 0
        if watched >= AD_DAILY_LIMIT:
            raise HTTPException(status_code=400, detail="오늘 광고 시청 횟수를 초과했습니다.")

        cur.execute(
            """
            UPDATE users SET ad_watched_today = ?, last_ad_date = ?
             WHERE id = ?
               AND (last_ad_date != ? OR last_ad_date IS NULL OR ad_watched_today = ?)
            """,
            (watched + 1, today, uid, today, watched),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=409, detail="처리 중입니다. 잠시 후 다시 시도해주세요.")

        expires_at = ts.silver_expiry(EVENT_EXPIRE_DAYS)
        ts.grant(cur, uid, AD_TOKEN, ts.SILVER, "광고 시청", expires_at,
                 idempotency_key=f"ad:{uid}:{today}:{watched + 1}")

    return {
        "message": f"광고 시청 완료! {AD_TOKEN}토큰 지급 ({EVENT_EXPIRE_DAYS}일 유효)",
        "remaining_today": AD_DAILY_LIMIT - (watched + 1),
        "expires_at": expires_at.strftime("%Y-%m-%d"),
    }


# ── 구매 ────────────────────────────────────────────────────────────────
# 경고: PG 연동 전까지 아래 엔드포인트는 관리자 전용이다.
# 일반 유저에게 열려 있던 시절에는 로그인만으로 무한 충전이 가능했다.
# PG 연동 시에는 이 함수를 지우고 webhook 에서 아래를 모두 검증해야 한다:
#   1) PG 서명 검증  2) 결제 금액 == package["price"]  3) merchant_uid 멱등
@router.post("/purchase/{package_id}", summary="[관리자] 토큰 지급 (PG 연동 전 임시)")
def purchase_token(
    package_id: int,
    target_user_id: int,
    admin: dict = Depends(require_admin),
):
    package = next((p for p in TOKEN_PACKAGES if p["id"] == package_id), None)
    if not package:
        raise HTTPException(status_code=404, detail="패키지를 찾을 수 없습니다.")

    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    with transaction() as cur:
        cur.execute(
            "SELECT consecutive_purchase_days, last_purchase_date FROM users WHERE id = ?",
            (target_user_id,),
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        last_date = user["last_purchase_date"]
        consecutive = user["consecutive_purchase_days"] or 0
        if last_date == yesterday:
            consecutive += 1
        elif last_date != today:
            consecutive = 1

        payback = 0
        if consecutive >= 5:
            payback = package["token_amount"] // 2
            consecutive = 0

        cur.execute(
            "INSERT INTO purchases (user_id, amount, token_amount, payment_method, status) "
            "VALUES (?, ?, ?, 'admin', 'completed')",
            (target_user_id, package["price"], package["token_amount"]),
        )
        purchase_id = cur.lastrowid

        ts.grant(cur, target_user_id, package["token_amount"], ts.GOLD,
                 f"토큰 구매 ({package['label']})",
                 datetime.now() + timedelta(days=365),
                 idempotency_key=f"purchase:{purchase_id}")

        if payback > 0:
            ts.grant(cur, target_user_id, payback, ts.SILVER, "5일 연속 구매 페이백",
                     ts.silver_expiry(EVENT_EXPIRE_DAYS),
                     idempotency_key=f"payback:{purchase_id}")

        cur.execute(
            "UPDATE users SET consecutive_purchase_days = ?, last_purchase_date = ? WHERE id = ?",
            (consecutive, today, target_user_id),
        )

    result = {
        "message": f"지급 완료! {package['token_amount']}토큰",
        "token_amount": package["token_amount"],
        "consecutive_days": consecutive,
    }
    if payback > 0:
        result["payback"] = payback
    return result


# ── 메모리 패스 ─────────────────────────────────────────────────────────
def _extend_expiry(current: str | None, days: int) -> datetime:
    now = datetime.now()
    base = now
    if current:
        try:
            existing = datetime.fromisoformat(current)
            base = existing if existing > now else now
        except ValueError:
            base = now
    return base + timedelta(days=days)


@router.post("/memory-pass/purchase", summary="메모리 패스 구매 (금화)")
def purchase_memory_pass(current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with transaction() as cur:
        cur.execute(
            "SELECT token_purchased, memory_pass_expires_at, memory_chunk_limit "
            "FROM users WHERE id = ?", (uid,)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        new_expires = _extend_expiry(user["memory_pass_expires_at"], 30)

        # 금화 한정 차감 + 패스 연장을 한 UPDATE 로 묶어 원자화
        cur.execute(
            """
            UPDATE users
               SET token_purchased = token_purchased - ?,
                   token_balance   = token_purchased + token_event - ?,
                   memory_pass_expires_at = ?,
                   memory_chunk_limit = MIN(?, COALESCE(memory_chunk_limit, 20) + 5)
             WHERE id = ? AND token_purchased >= ?
            """,
            (MEMORY_PASS_30DAY_COINS, MEMORY_PASS_30DAY_COINS, new_expires.isoformat(),
             MEMORY_CHUNK_MAX, uid, MEMORY_PASS_30DAY_COINS),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=402, detail="금화가 부족해요. 금화로만 구매 가능해요.")

        cur.execute(
            "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, ?, ?, ?)",
            (uid, -MEMORY_PASS_30DAY_COINS, ts.GOLD, "메모리 패스 30일권 금화 구매 (+청크 5개)"),
        )

    return {
        "message": "메모리 패스 30일권 구매 완료 (보너스 청크 5개 지급)",
        "expires_at": new_expires.strftime("%Y-%m-%d"),
    }


# PG 연동 전까지 관리자 전용. 이전에는 결제 없이 누구나 30일권을 받을 수 있었다.
@router.post("/memory-pass/purchase-cash", summary="[관리자] 메모리 패스 현금 지급")
def purchase_memory_pass_cash(target_user_id: int, admin: dict = Depends(require_admin)):
    with transaction() as cur:
        cur.execute("SELECT memory_pass_expires_at FROM users WHERE id = ?", (target_user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        new_expires = _extend_expiry(user["memory_pass_expires_at"], 30)
        cur.execute(
            "UPDATE users SET memory_pass_expires_at = ? WHERE id = ?",
            (new_expires.isoformat(), target_user_id),
        )
        cur.execute(
            "INSERT INTO purchases (user_id, amount, token_amount, payment_method, status) "
            "VALUES (?, ?, 0, 'admin', 'completed')",
            (target_user_id, MEMORY_PASS_CASH_PRICE),
        )
        cur.execute(
            "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, 0, ?, ?)",
            (target_user_id, ts.GOLD, "메모리 패스 30일권 현금 구매"),
        )

    return {"message": "메모리 패스 30일권 지급 완료", "expires_at": new_expires.strftime("%Y-%m-%d")}


@router.get("/memory-pass/status", summary="메모리 패스 상태 확인")
def get_memory_pass_status(current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        cur.execute(
            "SELECT memory_pass_expires_at, memory_chunk_limit FROM users WHERE id = ?",
            (current_user["id"],),
        )
        user = cur.fetchone()

    expires_at = user["memory_pass_expires_at"] if user else None
    if not expires_at:
        return {"active": False, "expires_at": None, "chunk_limit": 0}

    try:
        active = datetime.fromisoformat(expires_at) > datetime.now()
    except ValueError:
        active = False

    return {
        "active": active,
        "expires_at": expires_at[:10],
        "chunk_limit": user["memory_chunk_limit"] or 20,
    }


@router.post("/memory-pass/add-chunk", summary="메모리 청크 추가 (금화)")
def add_memory_chunk(amount: int = 1, current_user: dict = Depends(get_current_user)):
    if amount < 1 or amount > 50:
        raise HTTPException(status_code=400, detail="1~50개 사이로 추가 가능해요.")

    uid = current_user["id"]
    with transaction() as cur:
        cur.execute(
            "SELECT memory_pass_expires_at, memory_chunk_limit FROM users WHERE id = ?", (uid,)
        )
        user = cur.fetchone()
        if not user or not user["memory_pass_expires_at"]:
            raise HTTPException(status_code=403, detail="메모리 패스가 없어요.")
        try:
            if datetime.fromisoformat(user["memory_pass_expires_at"]) <= datetime.now():
                raise HTTPException(status_code=403, detail="메모리 패스가 만료됐어요.")
        except ValueError:
            raise HTTPException(status_code=403, detail="메모리 패스가 만료됐어요.")

        current_limit = user["memory_chunk_limit"] or 20
        if current_limit + amount > MEMORY_CHUNK_MAX:
            raise HTTPException(status_code=400, detail=f"최대 {MEMORY_CHUNK_MAX}청크까지 추가 가능해요.")

        cur.execute(
            """
            UPDATE users
               SET token_purchased = token_purchased - ?,
                   token_balance   = token_purchased + token_event - ?,
                   memory_chunk_limit = memory_chunk_limit + ?
             WHERE id = ? AND token_purchased >= ?
            """,
            (amount, amount, amount, uid, amount),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=402, detail="금화가 부족해요.")

        cur.execute(
            "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, ?, ?, ?)",
            (uid, -amount, ts.GOLD, f"메모리 청크 {amount}개 추가"),
        )

    return {"message": f"메모리 청크 {amount}개 추가 완료", "new_limit": current_limit + amount}
