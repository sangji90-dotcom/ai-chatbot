from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from deps import get_current_user
from typing import Optional

router = APIRouter(prefix="/admin", tags=["관리자"])


def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")
    return current_user


# ===== 통계 =====
@router.get("/stats", summary="전체 통계")
async def get_stats(admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    user_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM characters")
    char_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM chat_history WHERE role = 'user'")
    chat_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM character_reports WHERE status = 'pending'")
    pending_reports = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM inquiries WHERE status = 'pending'")
    pending_inquiries = cursor.fetchone()["cnt"]

    conn.close()
    return {
        "user_count": user_count,
        "character_count": char_count,
        "chat_count": chat_count,
        "pending_reports": pending_reports,
        "pending_inquiries": pending_inquiries
    }


# ===== 유저 관리 =====
@router.get("/users", summary="전체 유저 목록")
async def get_all_users(
        page: int = 1,
        size: int = 20,
        q: Optional[str] = None,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    if q:
        cursor.execute("""
            SELECT id, email, username, is_admin, is_adult, safety_mode,
                   token_balance, attendance_streak, created_at,
                   suspended
            FROM users WHERE username LIKE ? OR email LIKE ?
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (f"%{q}%", f"%{q}%", size, (page - 1) * size))
    else:
        cursor.execute("""
            SELECT id, email, username, is_admin, is_adult, safety_mode,
                   token_balance, attendance_streak, created_at,
                   suspended
            FROM users
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (size, (page - 1) * size))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/users/{user_id}/suspend", summary="유저 정지")
async def suspend_user(
        user_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    cursor.execute("UPDATE users SET suspended = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "유저 정지 완료"}


@router.patch("/users/{user_id}/unsuspend", summary="유저 정지 해제")
async def unsuspend_user(
        user_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET suspended = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "유저 정지 해제 완료"}


@router.patch("/users/{user_id}/grant-admin", summary="관리자 권한 부여")
async def grant_admin(
        user_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "관리자 권한 부여 완료"}


@router.patch("/users/{user_id}/revoke-admin", summary="관리자 권한 해제")
async def revoke_admin(
        user_id: int,
        admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="본인 권한은 해제할 수 없습니다.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "관리자 권한 해제 완료"}


# ===== 신고 관리 =====
@router.get("/reports", summary="신고 목록")
async def get_reports(
        status: Optional[str] = "pending",
        page: int = 1,
        size: int = 20,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cr.*, u.username as reporter_name,
               c.name as character_name, c.user_id as character_owner_id
        FROM character_reports cr
        JOIN users u ON cr.user_id = u.id
        JOIN characters c ON cr.character_id = c.id
        WHERE cr.status = ?
        ORDER BY cr.created_at DESC
        LIMIT ? OFFSET ?
    """, (status, size, (page - 1) * size))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/reports/{report_id}/dismiss", summary="신고 무시")
async def dismiss_report(
        report_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE character_reports SET status = 'dismissed' WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
    return {"message": "신고 무시 완료"}


@router.patch("/reports/{report_id}/action", summary="신고 처리 (캐릭터 삭제)")
async def action_report(
        report_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM character_reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        raise HTTPException(status_code=404, detail="신고를 찾을 수 없습니다.")

    # 캐릭터 삭제
    cursor.execute("DELETE FROM character_tags WHERE character_id = ?", (report["character_id"],))
    cursor.execute("DELETE FROM characters WHERE id = ?", (report["character_id"],))
    cursor.execute("UPDATE character_reports SET status = 'actioned' WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
    return {"message": "신고 처리 완료 (캐릭터 삭제됨)"}


# ===== 문의 관리 =====
@router.get("/inquiries", summary="문의 목록")
async def get_all_inquiries(
        status: Optional[str] = "pending",
        page: int = 1,
        size: int = 20,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, u.username as username, u.email as email
        FROM inquiries i
        LEFT JOIN users u ON i.user_id = u.id
        WHERE i.status = ?
        ORDER BY i.created_at DESC
        LIMIT ? OFFSET ?
    """, (status, size, (page - 1) * size))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


class AnswerRequest(BaseModel):
    answer: str

@router.patch("/inquiries/{inquiry_id}/answer", summary="문의 답변")
async def answer_inquiry(
        inquiry_id: int,
        request: AnswerRequest,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE inquiries SET answer = ?, status = 'answered' WHERE id = ?
    """, (request.answer, inquiry_id))
    conn.commit()
    conn.close()
    return {"message": "답변 완료"}


# ===== 공식 스토리 등록 =====
@router.patch("/stories/{story_id}/official", summary="공식 스토리 지정")
async def set_official_story(
        story_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE stories SET is_official = 1 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()
    return {"message": "공식 스토리 지정 완료"}


@router.patch("/stories/{story_id}/unofficial", summary="공식 스토리 해제")
async def unset_official_story(
        story_id: int,
        admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE stories SET is_official = 0 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()
    return {"message": "공식 스토리 해제 완료"}


# ===== 토큰 지급 =====
class TokenGrantRequest(BaseModel):
    amount: int
    reason: str

@router.post("/users/{user_id}/grant-token", summary="토큰 지급")
async def grant_token(
        user_id: int,
        request: TokenGrantRequest,
        admin: dict = Depends(require_admin)):
    from notifications.router import send_notification
    from tokens.router import add_token
    from datetime import datetime, timedelta

    expires_at = datetime.now() + timedelta(days=30)
    add_token(user_id, request.amount, "event", f"관리자 지급: {request.reason}", expires_at)

    send_notification(
        user_id,
        "token_grant",
        "토큰이 지급됐어요!",
        f"{request.amount}토큰이 지급됐습니다. 사유: {request.reason}",
        "/tokens/me"
    )

    return {"message": f"{request.amount}토큰 지급 완료"}