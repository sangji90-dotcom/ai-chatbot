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


@router.get("", summary="알림 목록")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.get("/unread-count", summary="미읽음 알림 수")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count FROM notifications
        WHERE user_id = ? AND is_read = 0
    """, (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    return {"count": row["count"]}


@router.patch("/read-all", summary="전체 알림 읽음 처리")
async def read_all_notifications(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET is_read = 1
        WHERE user_id = ?
    """, (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "전체 읽음 처리 완료"}


@router.patch("/{notification_id}/read", summary="알림 읽음 처리")
async def read_notification(
        notification_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET is_read = 1
        WHERE id = ? AND user_id = ?
    """, (notification_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "읽음 처리 완료"}


@router.delete("", summary="전체 알림 삭제")
async def delete_all_notifications(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE user_id = ?", (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "전체 알림 삭제 완료"}

@router.delete("/{notification_id}", summary="알림 삭제")
async def delete_notification(
        notification_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM notifications WHERE id = ? AND user_id = ?
    """, (notification_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "알림 삭제 완료"}