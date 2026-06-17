from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from deps import get_current_user
from datetime import date, datetime, timedelta

router = APIRouter(
    prefix="/tokens",
    tags=["토큰"],
    responses={404: {"description": "찾을 수 없습니다"}}
)

# 토큰 설정
SIGNUP_TOKEN = 3000          # 회원가입 기본 지급
ATTENDANCE_TOKEN = 1000      # 출석 체크 지급
AD_TOKEN = 500               # 광고 시청 지급
AD_DAILY_LIMIT = 2           # 하루 광고 최대 횟수
CHAT_DEDUCT = 50             # 대화 1회 차감
EVENT_EXPIRE_DAYS = 21       # 이벤트 토큰 유효기간

# 토큰 패키지
TOKEN_PACKAGES = [
    {"id": 1, "price": 1900, "token_amount": 2000, "label": "2,000토큰"},
    {"id": 2, "price": 3800, "token_amount": 4200, "label": "4,200토큰 (+200 보너스)"},
    {"id": 3, "price": 9500, "token_amount": 11000, "label": "11,000토큰 (+1,000 보너스)"},
    {"id": 4, "price": 19000, "token_amount": 23000, "label": "23,000토큰 (+3,000 보너스)"},
]


def add_token(user_id: int, amount: int, token_type: str, reason: str, expires_at=None):
    conn = get_db()
    cursor = conn.cursor()
    if token_type == "event":
        cursor.execute("""
            UPDATE users SET token_event = token_event + ?,
            token_balance = token_balance + ? WHERE id = ?
        """, (amount, amount, user_id))
    else:
        cursor.execute("""
            UPDATE users SET token_purchased = token_purchased + ?,
            token_balance = token_balance + ? WHERE id = ?
        """, (amount, amount, user_id))
    cursor.execute("""
        INSERT INTO token_history (user_id, amount, token_type, reason, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, token_type, reason, expires_at))
    conn.commit()
    conn.close()

def deduct_token(user_id: int, amount: int, reason: str):
    from notifications.router import send_notification
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT token_event, token_purchased, token_balance FROM users WHERE id = ?
    """, (user_id,))
    user = cursor.fetchone()

    if user["token_balance"] < amount:
        conn.close()
        send_notification(
             user_id,
            "token_empty",
            "토큰이 부족합니다",
            "토큰을 충전하고 대화를 계속해보세요!",
            "/tokens/packages"
        )
        raise HTTPException(status_code=400, detail="토큰이 부족합니다.")

    event = user["token_event"]
    purchased = user["token_purchased"]

    # 이벤트 토큰 먼저 차감
    if event >= amount:
        cursor.execute("""
            UPDATE users SET token_event = token_event - ?,
            token_balance = token_balance - ? WHERE id = ?
        """, (amount, amount, user_id))
    elif event > 0:
        remain = amount - event
        cursor.execute("""
            UPDATE users SET token_event = 0,
            token_purchased = token_purchased - ?,
            token_balance = token_balance - ? WHERE id = ?
        """, (remain, amount, user_id))
    else:
        cursor.execute("""
            UPDATE users SET token_purchased = token_purchased - ?,
            token_balance = token_balance - ? WHERE id = ?
        """, (amount, amount, user_id))

    cursor.execute("""
        INSERT INTO token_history (user_id, amount, token_type, reason)
        VALUES (?, ?, ?, ?)
    """, (user_id, -amount, "use", reason))

    conn.commit()
    remaining = user["token_balance"] - amount
    if remaining <= 100:
        send_notification(
            user_id,
            "token_low",
            "토큰이 거의 소진됐어요",
            f"잔여 토큰: {remaining}개. 지금 충전하면 대화가 끊기지 않아요!",
            "/tokens/packages"
        )
    conn.close()

@router.get("/packages", summary="토큰 패키지 목록", description="구매 가능한 토큰 패키지 목록을 반환합니다.")
async def get_packages():
    return TOKEN_PACKAGES

@router.get("/me", summary="내 토큰 조회", description="보유 토큰 (구매/이벤트/총합)을 반환합니다.")
async def get_my_tokens(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT token_purchased, token_event, token_balance FROM users WHERE id = ?
    """, (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.get("/me/history", summary="토큰 내역", description="토큰 충전/사용 내역을 반환합니다.")
async def get_token_history(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM token_history WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 50
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/attendance", summary="출석 체크", description="출석 체크 후 이벤트 토큰을 지급합니다. (21일 유효)")
async def attendance_check(current_user: dict = Depends(get_current_user)):
    today = str(date.today())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT last_attendance_date FROM users WHERE id = ?", (current_user["id"],))
    user = cursor.fetchone()
    conn.close()

    if user["last_attendance_date"] == today:
        raise HTTPException(status_code=400, detail="오늘 이미 출석했습니다.")

    expires_at = datetime.now() + timedelta(days=EVENT_EXPIRE_DAYS)
    add_token(current_user["id"], ATTENDANCE_TOKEN, "event", "출석 체크", expires_at)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET last_attendance_date = ?,
        attendance_streak = attendance_streak + 1 WHERE id = ?
    """, (today, current_user["id"]))
    conn.commit()
    conn.close()

    return {
        "message": f"출석 완료! {ATTENDANCE_TOKEN}토큰 지급 (21일 유효)",
        "expires_at": expires_at.strftime("%Y-%m-%d")
    }

@router.post("/ad-watch", summary="광고 시청", description="광고 시청 후 이벤트 토큰을 지급합니다. 하루 2회 제한. (21일 유효)")
async def watch_ad(current_user: dict = Depends(get_current_user)):
    today = str(date.today())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ad_watched_today, last_ad_date FROM users WHERE id = ?",
                   (current_user["id"],))
    user = cursor.fetchone()
    conn.close()

    watched = user["ad_watched_today"] if user["last_ad_date"] == today else 0

    if watched >= AD_DAILY_LIMIT:
        raise HTTPException(status_code=400, detail="오늘 광고 시청 횟수를 초과했습니다.")

    expires_at = datetime.now() + timedelta(days=EVENT_EXPIRE_DAYS)
    add_token(current_user["id"], AD_TOKEN, "event", "광고 시청", expires_at)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET ad_watched_today = ?, last_ad_date = ? WHERE id = ?
    """, (watched + 1, today, current_user["id"]))
    conn.commit()
    conn.close()

    return {
        "message": f"광고 시청 완료! {AD_TOKEN}토큰 지급 (21일 유효)",
        "remaining_today": AD_DAILY_LIMIT - (watched + 1),
        "expires_at": expires_at.strftime("%Y-%m-%d")
    }

@router.post("/purchase/{package_id}", summary="토큰 구매", description="토큰 패키지를 구매합니다. (실제 결제 연동 전 테스트용)")
async def purchase_token(
        package_id: int,
        current_user: dict = Depends(get_current_user)):
    package = next((p for p in TOKEN_PACKAGES if p["id"] == package_id), None)
    if not package:
        raise HTTPException(status_code=404, detail="패키지를 찾을 수 없습니다.")

    today = str(date.today())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT consecutive_purchase_days, last_purchase_date FROM users WHERE id = ?
    """, (current_user["id"],))
    user = cursor.fetchone()
    conn.close()

    # 연속 구매 카운트
    last_date = user["last_purchase_date"]
    consecutive = user["consecutive_purchase_days"]

    from datetime import timedelta
    yesterday = str((date.today() - timedelta(days=1)))

    if last_date == yesterday:
        consecutive += 1
    elif last_date == today:
        consecutive = consecutive  # 오늘 이미 구매
    else:
        consecutive = 1  # 리셋

    # 5일 연속 구매 페이백
    payback = 0
    if consecutive >= 5:
        payback = package["token_amount"] // 2
        consecutive = 0  # 리셋

    expires_at = datetime.now() + timedelta(days=365)
    add_token(current_user["id"], package["token_amount"], "purchased",
              f"토큰 구매 ({package['label']})", expires_at)

    if payback > 0:
        add_token(current_user["id"], payback, "event",
                  "5일 연속 구매 페이백", datetime.now() + timedelta(days=EVENT_EXPIRE_DAYS))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET consecutive_purchase_days = ?,
        last_purchase_date = ? WHERE id = ?
    """, (consecutive, today, current_user["id"]))

    cursor.execute("""
        INSERT INTO purchases (user_id, amount, token_amount, status)
        VALUES (?, ?, ?, ?)
    """, (current_user["id"], package["price"], package["token_amount"], "completed"))
    conn.commit()
    conn.close()

    result = {
        "message": f"구매 완료! {package['token_amount']}토큰 지급",
        "token_amount": package["token_amount"],
        "consecutive_days": consecutive
    }

    if payback > 0:
        result["payback"] = payback
        result["message"] += f" + 페이백 {payback}토큰!"

    return result

MEMORY_PASS_30DAY_COINS = 24900

@router.post("/memory-pass/purchase", summary="메모리 패스 구매 (금화)")
async def purchase_memory_pass(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT token_purchased, token_balance, memory_pass_expires_at FROM users WHERE id = ?",
                   (current_user["id"],))
    user = cursor.fetchone()

    if user["token_purchased"] < MEMORY_PASS_30DAY_COINS:
        conn.close()
        raise HTTPException(status_code=400, detail="금화가 부족해요. 금화로만 구매 가능해요.")

    now = datetime.now()
    if user["memory_pass_expires_at"]:
        try:
            existing = datetime.fromisoformat(user["memory_pass_expires_at"])
            base = existing if existing > now else now
        except:
            base = now
    else:
        base = now

    new_expires = base + timedelta(days=30)

    cursor.execute("""
        UPDATE users
        SET token_purchased = token_purchased - ?,
            token_balance = token_balance - ?,
            memory_pass_expires_at = ?
        WHERE id = ?
    """, (MEMORY_PASS_30DAY_COINS, MEMORY_PASS_30DAY_COINS,
          new_expires.isoformat(), current_user["id"]))

    cursor.execute("""
        INSERT INTO token_history (user_id, amount, token_type, reason)
        VALUES (?, ?, ?, ?)
    """, (current_user["id"], -MEMORY_PASS_30DAY_COINS, "purchased", "메모리 패스 30일권 구매"))

    conn.commit()
    conn.close()

    return {
        "message": "메모리 패스 30일권 구매 완료",
        "expires_at": new_expires.strftime("%Y-%m-%d"),
    }


@router.get("/memory-pass/status", summary="메모리 패스 상태 확인")
async def get_memory_pass_status(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT memory_pass_expires_at, memory_chunk_limit FROM users WHERE id = ?",
                   (current_user["id"],))
    user = cursor.fetchone()
    conn.close()

    expires_at = user["memory_pass_expires_at"]
    if not expires_at:
        return {"active": False, "expires_at": None, "chunk_limit": 0}

    try:
        expires = datetime.fromisoformat(expires_at)
        active = expires > datetime.now()
    except:
        active = False

    return {
        "active": active,
        "expires_at": expires_at[:10] if expires_at else None,
        "chunk_limit": user["memory_chunk_limit"] or 20,
    }


@router.post("/memory-pass/add-chunk", summary="메모리 청크 추가 (금화)")
async def add_memory_chunk(
        amount: int = 1,
        current_user: dict = Depends(get_current_user)):
    if amount < 1 or amount > 50:
        raise HTTPException(status_code=400, detail="1~50개 사이로 추가 가능해요.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT memory_pass_expires_at, token_purchased, token_balance, memory_chunk_limit
        FROM users WHERE id = ?
    """, (current_user["id"],))
    user = cursor.fetchone()

    if not user["memory_pass_expires_at"]:
        conn.close()
        raise HTTPException(status_code=403, detail="메모리 패스가 없어요.")

    try:
        expires = datetime.fromisoformat(user["memory_pass_expires_at"])
        if expires <= datetime.now():
            conn.close()
            raise HTTPException(status_code=403, detail="메모리 패스가 만료됐어요.")
    except ValueError:
        conn.close()
        raise HTTPException(status_code=403, detail="메모리 패스가 만료됐어요.")

    cost = amount  # 금화 1개 = 청크 1개
    if user["token_purchased"] < cost:
        conn.close()
        raise HTTPException(status_code=400, detail="금화가 부족해요.")

    current_limit = user["memory_chunk_limit"] or 20
    if current_limit + amount > 100:
        conn.close()
        raise HTTPException(status_code=400, detail="최대 100청크까지 추가 가능해요.")

    cursor.execute("""
        UPDATE users
        SET token_purchased = token_purchased - ?,
            token_balance = token_balance - ?,
            memory_chunk_limit = memory_chunk_limit + ?
        WHERE id = ?
    """, (cost, cost, amount, current_user["id"]))
    conn.commit()
    conn.close()

    return {
        "message": f"메모리 청크 {amount}개 추가 완료",
        "new_limit": current_limit + amount,
    }