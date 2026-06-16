from apscheduler.schedulers.background import BackgroundScheduler
from database import get_db
from datetime import datetime

def expire_tokens():
    """만료된 이벤트 토큰 정리"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 만료된 이벤트 토큰 내역 조회
    cursor.execute("""
        SELECT user_id, SUM(amount) as total_expired
        FROM token_history
        WHERE token_type = 'event'
          AND expires_at IS NOT NULL
          AND expires_at < ?
          AND amount > 0
        GROUP BY user_id
    """, (now,))
    expired_rows = cursor.fetchall()

    for row in expired_rows:
        user_id = row["user_id"]
        expired_amount = row["total_expired"]

        # 유저 현재 토큰 조회
        cursor.execute("""
            SELECT token_event, token_balance FROM users WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()
        if not user:
            continue

        # 실제 차감 (음수 방지)
        deduct = min(expired_amount, user["token_event"])
        if deduct <= 0:
            continue

        cursor.execute("""
            UPDATE users
            SET token_event = token_event - ?,
                token_balance = token_balance - ?
            WHERE id = ?
        """, (deduct, deduct, user_id))

        cursor.execute("""
            INSERT INTO token_history (user_id, amount, token_type, reason)
            VALUES (?, ?, 'expire', '이벤트 토큰 만료')
        """, (user_id, -deduct))

    # 만료된 토큰 내역 expires_at 무효화 (중복 처리 방지)
    cursor.execute("""
        UPDATE token_history
        SET expires_at = NULL
        WHERE token_type = 'event'
          AND expires_at IS NOT NULL
          AND expires_at < ?
          AND amount > 0
    """, (now,))

    conn.commit()
    conn.close()


def expire_refresh_tokens():
    """만료된 refresh token 정리"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM refresh_tokens WHERE expires_at < ?", (now,))
    conn.commit()
    conn.close()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_job(expire_tokens, "cron", hour=0, minute=0)        # 매일 자정
    scheduler.add_job(expire_refresh_tokens, "cron", hour=3, minute=0) # 매일 새벽 3시
    scheduler.start()