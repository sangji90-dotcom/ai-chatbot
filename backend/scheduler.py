from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_db
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()

# ===== 토큰 만료 처리 =====
def expire_tokens():
    now = datetime.now()
    conn = get_db()
    cursor = conn.cursor()

    # 만료된 이벤트 토큰 내역 조회
    cursor.execute("""
        SELECT user_id, SUM(amount) as total
        FROM token_history
        WHERE expires_at IS NOT NULL
        AND expires_at < ?
        AND amount > 0
        AND token_type = 'event'
        AND id NOT IN (
            SELECT COALESCE(ref_id, -1) FROM token_history WHERE token_type = 'expired'
        )
        GROUP BY user_id
    """, (now,))
    rows = cursor.fetchall()

    for row in rows:
        user_id = row["user_id"]
        expired_amount = row["total"]

        # 유저 이벤트 토큰 차감
        cursor.execute("""
            SELECT token_event FROM users WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            continue

        deduct = min(user["token_event"], expired_amount)
        if deduct > 0:
            cursor.execute("""
                UPDATE users SET
                token_event = token_event - ?,
                token_balance = token_balance - ?
                WHERE id = ?
            """, (deduct, deduct, user_id))
            cursor.execute("""
                INSERT INTO token_history (user_id, amount, token_type, reason)
                VALUES (?, ?, 'expired', '이벤트 토큰 만료')
            """, (user_id, -deduct))

    conn.commit()
    conn.close()

# ===== 가입 기념일 업적 =====
def check_anniversary_achievements():
    from achievements.router import check_and_grant

    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().date()

    cursor.execute("SELECT id, created_at FROM users")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        if not user["created_at"]:
            continue

        created = datetime.strptime(user["created_at"][:10], "%Y-%m-%d").date()
        days = (today - created).days

        if days == 30:
            check_and_grant(user["id"], "anniversary_30")
        elif days == 100:
            check_and_grant(user["id"], "anniversary_100")
        elif days == 365:
            check_and_grant(user["id"], "anniversary_365")
        elif days == 730:
            check_and_grant(user["id"], "anniversary_730")

def start_scheduler():
    scheduler.add_job(expire_tokens, "interval", hours=1)
    scheduler.add_job(check_anniversary_achievements, "cron", hour=0, minute=0)
    scheduler.start()