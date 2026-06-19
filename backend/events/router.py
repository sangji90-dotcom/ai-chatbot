from fastapi import APIRouter, Depends, Request, HTTPException
from deps import get_current_user
from database import get_db
import random
import string
from datetime import datetime, date, timedelta

router = APIRouter(prefix="/events", tags=["이벤트"])

# ── 초대 코드 생성 (유저당 1개 고정) ──────────────────────────
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@router.get("/referral-code")
def get_referral_code(current_user=Depends(get_current_user)):
    db = get_db()
    row = db.execute(
        "SELECT code FROM referral_codes WHERE user_id = ?", (current_user["id"],)
    ).fetchone()

    if row:
        return {"code": row["code"]}

    # 없으면 생성
    while True:
        code = generate_code()
        exists = db.execute(
            "SELECT id FROM referral_codes WHERE code = ?", (code,)
        ).fetchone()
        if not exists:
            break

    db.execute(
        "INSERT INTO referral_codes (user_id, code) VALUES (?, ?)",
        (current_user["id"], code)
    )
    db.commit()
    return {"code": code}


# ── 초대 코드 사용 (가입 후 1회) ──────────────────────────────
@router.post("/referral/use")
def use_referral_code(body: dict, request: Request, current_user=Depends(get_current_user)):
    code = body.get("code", "").strip().upper()
    if not code:
        raise HTTPException(400, "초대 코드를 입력해주세요.")

    db = get_db()
    referred_ip = request.client.host

    # 이미 초대 코드 사용했는지
    already = db.execute(
        "SELECT id FROM referrals WHERE referred_id = ?", (current_user["id"],)
    ).fetchone()
    if already:
        raise HTTPException(400, "이미 초대 코드를 사용했습니다.")

    # 코드 유효성
    code_row = db.execute(
        "SELECT user_id FROM referral_codes WHERE code = ?", (code,)
    ).fetchone()
    if not code_row:
        raise HTTPException(404, "유효하지 않은 초대 코드입니다.")

    referrer_id = code_row["user_id"]
    if referrer_id == current_user["id"]:
        raise HTTPException(400, "본인 초대 코드는 사용할 수 없습니다.")

    # IP 어뷰징 체크 (동일 IP 3개 초과)
    referrer_user = db.execute(
        "SELECT id FROM users WHERE id = ?", (referrer_id,)
    ).fetchone()
    referrer_ip_row = db.execute(
        "SELECT referred_ip FROM referrals WHERE referrer_id = ?", (referrer_id,)
    ).fetchone()

    same_ip_count = db.execute(
        "SELECT COUNT(*) as cnt FROM referrals WHERE referred_ip = ?", (referred_ip,)
    ).fetchone()["cnt"]
    if same_ip_count >= 3:
        raise HTTPException(400, "초대 보상을 받을 수 없습니다.")

    # 이메일 정규화 어뷰징 체크
    def normalize_email(email: str) -> str:
        local, domain = email.split("@")
        local = local.split("+")[0].replace(".", "")
        return f"{local}@{domain}"

    current_email_norm = normalize_email(current_user["email"])
    referrer_email = db.execute(
        "SELECT email FROM users WHERE id = ?", (referrer_id,)
    ).fetchone()["email"]
    referrer_email_norm = normalize_email(referrer_email)

    if current_email_norm == referrer_email_norm:
        raise HTTPException(400, "초대 보상을 받을 수 없습니다.")

    # referrals 등록
    referrer_ip_val = db.execute(
        "SELECT referrer_ip FROM referrals WHERE referrer_id = ? LIMIT 1", (referrer_id,)
    ).fetchone()
    r_ip = referrer_ip_val["referrer_ip"] if referrer_ip_val else referred_ip

    db.execute(
        "INSERT INTO referrals (referrer_id, referred_id, referrer_ip, referred_ip, reward_given) VALUES (?, ?, ?, ?, 1)",
        (referrer_id, current_user["id"], r_ip, referred_ip)
    )

    now = datetime.utcnow().isoformat()

    # 피초대자 금화 300
    db.execute(
        "UPDATE users SET token_purchased = token_purchased + 300 WHERE id = ?",
        (current_user["id"],)
    )
    db.execute(
        "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, 300, 'gold', '친구 초대 수락 보상')",
        (current_user["id"],)
    )

    # 초대자 금화 500
    db.execute(
        "UPDATE users SET token_purchased = token_purchased + 500 WHERE id = ?",
        (referrer_id,)
    )
    db.execute(
        "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, 500, 'gold', '친구 초대 보상')",
        (referrer_id,)
    )

    # 초대자 알림
    db.execute(
        "INSERT INTO notifications (user_id, type, title, message) VALUES (?, 'reward', '친구 초대 보상', '초대한 친구가 가입했습니다! 금화 500개가 지급되었습니다.')",
        (referrer_id,)
    )

    db.commit()
    return {"message": "초대 코드 적용 완료. 금화 300개가 지급되었습니다."}


# ── 7일 연속 출석 보상 체크 ────────────────────────────────────
@router.post("/attendance-streak-reward")
def claim_streak_reward(current_user=Depends(get_current_user)):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (current_user["id"],)).fetchone()

    if user["attendance_streak"] < 7:
        raise HTTPException(400, "7일 연속 출석이 필요합니다.")

    # 오늘 이미 수령했는지 (streak 달성 후 1회만)
    claimed = user["streak_reward_claimed_at"]
    if claimed:
        claimed_date = datetime.fromisoformat(claimed).date()
        # 마지막 출석일 기준으로 이미 지급됐으면 차단
        last_att = user["last_attendance_date"]
        if last_att and claimed_date == date.fromisoformat(last_att):
            raise HTTPException(400, "이미 보상을 수령했습니다.")

    now = datetime.utcnow()

    # 은화 5000 지급 (token_event)
    db.execute(
        "UPDATE users SET token_event = token_event + 5000, streak_reward_claimed_at = ? WHERE id = ?",
        (now.isoformat(), current_user["id"])
    )
    db.execute(
        "INSERT INTO token_history (user_id, amount, token_type, reason, expires_at) VALUES (?, 5000, 'silver', '7일 연속 출석 보상', ?)",
        (current_user["id"], (now + timedelta(days=21)).isoformat())
    )
    db.execute(
        "INSERT INTO notifications (user_id, type, title, message) VALUES (?, 'reward', '7일 개근 달성!', '은화 5,000개가 지급되었습니다. 21일 내 사용하세요!')",
        (current_user["id"],)
    )

    db.commit()
    return {"message": "은화 5,000개 지급 완료!", "expires_in_days": 21}


# ── 5일 연속 결제 보상 ─────────────────────────────────────────
def check_payment_streak(user_id: int, purchased_tokens: int, db):
    """구매 완료 시 호출. purchases 라우터에서 import해서 사용."""
    today = date.today().isoformat()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    last_purchase = user["last_purchase_date"]
    streak = user["consecutive_purchase_days"]
    streak_total = user["purchase_streak_total_tokens"]
    streak_start = user["consecutive_purchase_start_date"]

    if last_purchase == today:
        # 오늘 이미 구매함 → streak 유지, total만 누적
        db.execute(
            "UPDATE users SET purchase_streak_total_tokens = purchase_streak_total_tokens + ? WHERE id = ?",
            (purchased_tokens, user_id)
        )
        return

    yesterday = (date.today() - timedelta(days=1)).isoformat()

    if last_purchase == yesterday:
        # 연속
        new_streak = streak + 1
        new_total = streak_total + purchased_tokens
        new_start = streak_start or today
    else:
        # 끊김 → 리셋
        new_streak = 1
        new_total = purchased_tokens
        new_start = today

    db.execute(
        """UPDATE users SET
            consecutive_purchase_days = ?,
            last_purchase_date = ?,
            purchase_streak_total_tokens = ?,
            consecutive_purchase_start_date = ?
        WHERE id = ?""",
        (new_streak, today, new_total, new_start, user_id)
    )

    # 5일 달성 시 보상
    if new_streak == 5:
        avg = new_total // 5
        bonus = avg // 2  # 평균의 50%

        db.execute(
            "UPDATE users SET token_purchased = token_purchased + ?, consecutive_purchase_days = 0, purchase_streak_total_tokens = 0, consecutive_purchase_start_date = NULL WHERE id = ?",
            (bonus, user_id)
        )
        db.execute(
            "INSERT INTO token_history (user_id, amount, token_type, reason) VALUES (?, ?, 'gold', '5일 연속 결제 보상')",
            (user_id, bonus)
        )
        db.execute(
            "INSERT INTO notifications (user_id, type, title, message) VALUES (?, 'reward', '5일 연속 결제 달성!', ?)",
            (user_id, f"금화 {bonus:,}개가 추가 지급되었습니다!")
        )