from database import get_db

def send_notification(user_id: int, type: str, title: str, message: str, link: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, link)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, type, title, message, link))
    conn.commit()
    conn.close()