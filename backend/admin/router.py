from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from database import get_db
from core.db import read_only, transaction
from deps import get_current_user, require_admin  # require_admin 은 deps 로 일원화
from typing import Optional

router = APIRouter(prefix="/admin", tags=["관리자"])


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
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="본인 계정은 정지할 수 없습니다.")
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
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
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

    # 캐릭터 삭제 — 연관 레코드까지 정리 (FK CASCADE 가 없어 고아가 남던 문제)
    cid = report["character_id"]
    for stmt in (
        "DELETE FROM character_tags WHERE character_id = ?",
        "DELETE FROM character_images WHERE character_id = ?",
        "DELETE FROM character_backgrounds WHERE character_id = ?",
        "DELETE FROM character_likes WHERE character_id = ?",
        "DELETE FROM character_bookmarks WHERE character_id = ?",
        "DELETE FROM character_reviews WHERE character_id = ?",
        "DELETE FROM chat_history WHERE character_id = ?",
    ):
        try:
            cursor.execute(stmt, (cid,))
        except Exception:
            pass
    cursor.execute("DELETE FROM characters WHERE id = ?", (cid,))
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
    amount: int = Field(gt=0, le=1_000_000)
    reason: str = Field(min_length=1, max_length=200)

@router.post("/users/{user_id}/grant-token", summary="토큰 지급")
async def grant_token(
        user_id: int,
        request: TokenGrantRequest,
        admin: dict = Depends(require_admin)):
    from notifications.router import send_notification
    from tokens.router import add_token
    from datetime import datetime, timedelta

    import uuid as _uuid
    expires_at = datetime.now() + timedelta(days=30)
    add_token(user_id, request.amount, "event", f"관리자 지급: {request.reason}", expires_at,
              idempotency_key=f"admin-grant:{_uuid.uuid4().hex}")

    send_notification(
        user_id,
        "token_grant",
        "토큰이 지급됐어요!",
        f"{request.amount}토큰이 지급됐습니다. 사유: {request.reason}",
        "/tokens/me"
    )

    return {"message": f"{request.amount}토큰 지급 완료"}

# ===== 기억 품질 지표 =====
@router.get("/memory-stats", summary="기억 품질 지표")
async def memory_stats(days: int = 7, admin: dict = Depends(require_admin)):
    """"기억을 얼마나 잘하는가" 를 감이 아니라 숫자로 본다.

    - extract_rate: 추출을 시도한 구간 중 실제로 기억이 남은 비율.
      낮으면 프롬프트가 너무 보수적이거나 대화에 기억할 내용이 없다는 뜻.
    - forgot_reports: 유저가 직접 "기억 못한다" 고 신고한 횟수. 가장 직접적인 신호.
    - avg_injected: 요청당 주입된 기억 수. chunk 상한에 계속 붙어 있으면 상한이 병목.
    - summarize: 요약 발동 횟수. 요약 이후 forgot_reports 가 늘면 요약이 범인.
    """
    since = f"-{max(1, min(days, 90))} days"
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT event_type, COUNT(*) AS cnt, AVG(value) AS avg_value
          FROM memory_events
         WHERE created_at >= datetime('now', '{since}')
         GROUP BY event_type
    """)
    events = {r["event_type"]: {"count": r["cnt"], "avg_value": round(r["avg_value"] or 0, 2)}
              for r in cursor.fetchall()}

    extract_ok = events.get("extract", {}).get("count", 0)
    extract_empty = events.get("extract_empty", {}).get("count", 0)
    extract_fail = events.get("extract_fail", {}).get("count", 0)
    attempts = extract_ok + extract_empty + extract_fail

    cursor.execute(f"""
        SELECT reason, COUNT(*) AS cnt FROM message_ratings
         WHERE rating = 'dislike' AND created_at >= datetime('now', '{since}')
         GROUP BY reason
    """)
    dislike_reasons = {(r["reason"] or "unspecified"): r["cnt"] for r in cursor.fetchall()}

    cursor.execute(f"""
        SELECT COUNT(*) AS cnt FROM message_ratings
         WHERE rating = 'like' AND created_at >= datetime('now', '{since}')
    """)
    likes = cursor.fetchone()["cnt"]

    # 세션 길이 분포 — 기억이 의미를 갖는 구간(10턴 이상)에 얼마나 도달하는지
    cursor.execute(f"""
        SELECT
            SUM(CASE WHEN n < 10  THEN 1 ELSE 0 END) AS under_10,
            SUM(CASE WHEN n >= 10 AND n < 40  THEN 1 ELSE 0 END) AS turns_10_40,
            SUM(CASE WHEN n >= 40 AND n < 100 THEN 1 ELSE 0 END) AS turns_40_100,
            SUM(CASE WHEN n >= 100 THEN 1 ELSE 0 END) AS over_100,
            COUNT(*) AS sessions,
            AVG(n) AS avg_turns
        FROM (
            SELECT session_id, COUNT(*) AS n FROM chat_history
             WHERE role = 'user' AND created_at >= datetime('now', '{since}')
             GROUP BY session_id
        )
    """)
    sessions = dict(cursor.fetchone())

    cursor.execute("""
        SELECT COUNT(*) AS total,
               COUNT(DISTINCT user_id || ':' || character_id) AS pairs
          FROM memory_book
    """)
    book = dict(cursor.fetchone())

    conn.close()
    return {
        "period_days": days,
        "sessions": {k: (round(v, 1) if isinstance(v, float) else (v or 0))
                     for k, v in sessions.items()},
        "memory_book": book,
        "events": events,
        "extract_rate": round(extract_ok / attempts, 3) if attempts else None,
        "avg_injected": events.get("inject", {}).get("avg_value", 0),
        "forgot_reports": dislike_reasons.get("memory", 0),
        "feedback": {"likes": likes, "dislikes_by_reason": dislike_reasons},
    }


@router.get("/memory-stats/samples", summary="기억 신고 샘플")
async def memory_report_samples(limit: int = 20, admin: dict = Depends(require_admin)):
    """"기억 못한다" 신고가 달린 메시지의 전후 맥락. 원인 분석용."""
    limit = min(max(1, limit), 100)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT mr.message_id, mr.session_id, mr.user_id, mr.created_at,
               ch.character_id, ch.content AS reported_message
          FROM message_ratings mr
          JOIN chat_history ch ON mr.message_id = ch.id
         WHERE mr.rating = 'dislike' AND mr.reason = 'memory'
         ORDER BY mr.created_at DESC LIMIT ?
    """, (limit,))
    samples = []
    for r in cursor.fetchall():
        item = dict(r)
        cursor.execute("""
            SELECT role, content FROM chat_history
             WHERE session_id = ? AND id < ? ORDER BY id DESC LIMIT 6
        """, (r["session_id"], r["message_id"]))
        item["context_before"] = [dict(x) for x in reversed(cursor.fetchall())]
        cursor.execute("""
            SELECT content FROM memory_book
             WHERE user_id = ? AND character_id = ? ORDER BY id DESC LIMIT 20
        """, (r["user_id"], r["character_id"]))
        item["memories_at_the_time"] = [x["content"] for x in cursor.fetchall()]
        samples.append(item)
    conn.close()
    return samples
