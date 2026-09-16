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

def warn_expiring_silver_tokens():
    """은화 만료 D-3 경고 알림 (token_type 은 'event' — 기존엔 'silver' 로 조회해 항상 0건이었다)"""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now()
    # 3일 후 만료되는 은화 보유 유저
    three_days_later = (now + __import__('datetime').timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT user_id, SUM(amount) as total
        FROM token_history
        WHERE token_type = 'event'
          AND expires_at IS NOT NULL
          AND expires_at > ?
          AND expires_at <= ?
          AND amount > 0
        GROUP BY user_id
    """, (now.strftime("%Y-%m-%d %H:%M:%S"), three_days_later))
    rows = cursor.fetchall()

    for row in rows:
        user_id = row["user_id"]
        total = row["total"]

        # 오늘 이미 경고 알림 보냈는지 체크
        already = cursor.execute("""
            SELECT id FROM notifications
            WHERE user_id = ?
              AND type = 'warning'
              AND title = '은화 만료 예정'
              AND created_at >= ?
        """, (user_id, now.strftime("%Y-%m-%d 00:00:00"))).fetchone()
        if already:
            continue

        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message)
            VALUES (?, 'warning', '은화 만료 예정', ?)
        """, (user_id, f"은화 {total:,}개가 3일 후 만료됩니다. 지금 사용하세요!"))

    conn.commit()
    conn.close()


def check_anniversary_achievements():
    """가입 기념일 업적 체크 (기존에 있으면 스킵)"""
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%m-%d")

    cursor.execute("""
        SELECT id FROM users
        WHERE strftime('%m-%d', created_at) = ?
          AND suspended = 0
          AND created_at <= datetime('now', '-1 year')
    """, (today,))
    users = cursor.fetchall()

    for user in users:
        user_id = user["id"]
        already = cursor.execute("""
            SELECT id FROM user_achievements
            WHERE user_id = ? AND achievement_code = 'anniversary'
        """, (user_id,)).fetchone()
        if already:
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO user_achievements (user_id, achievement_code)
            VALUES (?, 'anniversary')
        """, (user_id,))
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message)
            VALUES (?, 'reward', '가입 기념일!', '함께한 지 1년이 됐어요! 기념 업적을 달성했습니다.')
        """, (user_id,))
        
    conn.commit()
    conn.close()

_scheduler = None


def start_scheduler():
    """주의: 이 스케줄러는 앱 프로세스 안에서 돈다.

    uvicorn --workers N 으로 띄우면 잡이 N번 실행되어 토큰 만료가 N중으로 차감된다.
    워커를 늘릴 때는 RUN_SCHEDULER=0 으로 두고 전용 프로세스에서만 켤 것.
    """
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.configure(job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600})
    scheduler.add_job(expire_tokens, "cron", hour=0, minute=0)
    scheduler.add_job(expire_refresh_tokens, "cron", hour=3, minute=0)
    scheduler.add_job(warn_expiring_silver_tokens, "cron", hour=10, minute=0)  # 매일 오전 10시
    scheduler.add_job(check_anniversary_achievements, "cron", hour=0, minute=5)
    scheduler.start()
    _scheduler = scheduler
    return scheduler