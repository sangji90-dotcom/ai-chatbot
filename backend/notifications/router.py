from fastapi import APIRouter, Depends
from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["알림"])

def send_notification(user_id: int, type: str, title: str, message: str, link: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, type, title, message, link))
    conn.commit()
    conn.close()

# 나머지 엔드포인트들...