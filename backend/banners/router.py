from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth.router import get_current_user

router = APIRouter(
    prefix="/banners",
    tags=["배너"],
    responses={404: {"description": "찾을 수 없습니다"}}
)

class BannerRequest(BaseModel):
    title: str
    image_url: str
    link_url: str = ""
    order_num: int = 0

@router.get("", summary="배너 목록", description="활성화된 배너 목록을 반환합니다.")
async def get_banners():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM banners WHERE is_active = 1 ORDER BY order_num ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("", summary="배너 등록 (관리자)", description="새 배너를 등록합니다.")
async def create_banner(
        request: BannerRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO banners (title, image_url, link_url, order_num)
        VALUES (?, ?, ?, ?)
    """, (request.title, request.image_url, request.link_url, request.order_num))
    conn.commit()
    banner_id = cursor.lastrowid
    conn.close()
    return {"id": banner_id, "message": "배너 등록 완료"}

@router.patch("/{banner_id}/toggle", summary="배너 ON/OFF (관리자)", description="배너 활성화 상태를 토글합니다.")
async def toggle_banner(
        banner_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_active FROM banners WHERE id = ?", (banner_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="배너를 찾을 수 없습니다.")
    cursor.execute("""
        UPDATE banners SET is_active = ? WHERE id = ?
    """, (0 if row["is_active"] else 1, banner_id))
    conn.commit()
    conn.close()
    return {"message": "배너 상태 변경 완료"}

@router.delete("/{banner_id}", summary="배너 삭제 (관리자)", description="배너를 삭제합니다.")
async def delete_banner(
        banner_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="배너를 찾을 수 없습니다.")
    conn.commit()
    conn.close()
    return {"message": "배너 삭제 완료"}