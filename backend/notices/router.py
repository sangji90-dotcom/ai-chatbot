from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from deps import get_current_user, get_optional_user
from typing import Optional

router = APIRouter(prefix="/notices", tags=["공지사항"])


class NoticeRequest(BaseModel):
    title: str
    content: str
    is_pinned: int = 0


@router.get("", summary="공지사항 목록")
async def get_notices(
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notices
        ORDER BY is_pinned DESC, created_at DESC
        LIMIT ? OFFSET ?
    """, (size, (page - 1) * size))
    rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as cnt FROM notices")
    total = cursor.fetchone()["cnt"]
    conn.close()

    return {
        "total": total,
        "notices": [dict(row) for row in rows]
    }


@router.get("/{notice_id}", summary="공지사항 상세")
async def get_notice(notice_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices WHERE id = ?", (notice_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    return dict(row)


@router.post("", summary="공지사항 등록 (관리자)")
async def create_notice(
        request: NoticeRequest,
        current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 등록할 수 있습니다.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notices (title, content, is_pinned)
        VALUES (?, ?, ?)
    """, (request.title, request.content, request.is_pinned))
    conn.commit()
    notice_id = cursor.lastrowid
    conn.close()
    return {"id": notice_id, "message": "공지사항 등록 완료"}


@router.patch("/{notice_id}", summary="공지사항 수정 (관리자)")
async def update_notice(
        notice_id: int,
        request: NoticeRequest,
        current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 수정할 수 있습니다.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notices SET title = ?, content = ?, is_pinned = ? WHERE id = ?
    """, (request.title, request.content, request.is_pinned, notice_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    conn.commit()
    conn.close()
    return {"message": "공지사항 수정 완료"}


@router.delete("/{notice_id}", summary="공지사항 삭제 (관리자)")
async def delete_notice(
        notice_id: int,
        current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="관리자만 삭제할 수 있습니다.")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
    conn.commit()
    conn.close()
    return {"message": "공지사항 삭제 완료"}