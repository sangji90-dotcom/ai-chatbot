from fastapi import APIRouter, Depends
from database import get_db
from core.db import read_only, transaction
from deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["알림"])


def send_notification(user_id: int, type: str, title: str, message: str, link: str = ""):
    """알림 전송은 부가 기능이다 — 실패해도 호출한 비즈니스 로직을 막지 않는다."""
    try:
        with transaction() as cur:
            cur.execute("""
                INSERT INTO notifications (user_id, type, title, message, link)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, type, title, message, link))
    except Exception:
        import logging
        logging.getLogger("notifications").warning(
            "알림 전송 실패 user=%s type=%s", user_id, type, exc_info=True
        )


@router.get("", summary="알림 목록")
async def get_notifications(
        limit: int = 50,
        before_id: int | None = None,
        current_user: dict = Depends(get_current_user)):
    limit = min(max(1, limit), 100)
    sql = "SELECT * FROM notifications WHERE user_id = ?"
    params: list = [current_user["id"]]
    if before_id:
        sql += " AND id < ?"
        params.append(before_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with read_only() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


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