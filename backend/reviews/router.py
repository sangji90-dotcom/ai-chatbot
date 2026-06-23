from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from deps import get_current_user, get_optional_user
from typing import Optional

router = APIRouter(prefix="/reviews", tags=["리뷰"])


class ReviewRequest(BaseModel):
    rating: int
    content: str = ""


@router.post("/{character_id}", summary="리뷰 작성/수정")
async def create_or_update_review(
        character_id: str,
        request: ReviewRequest,
        current_user: dict = Depends(get_current_user)):
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="별점은 1~5 사이여야 해요.")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM characters WHERE id = ?", (character_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")

    cursor.execute("SELECT id FROM character_reviews WHERE user_id = ? AND character_id = ?",
                   (current_user["id"], character_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE character_reviews SET rating = ?, content = ? WHERE id = ?
        """, (request.rating, request.content, existing["id"]))
        msg = "리뷰 수정 완료"
    else:
        cursor.execute("""
            INSERT INTO character_reviews (user_id, character_id, rating, content)
            VALUES (?, ?, ?, ?)
        """, (current_user["id"], character_id, request.rating, request.content))
        msg = "리뷰 작성 완료"

    conn.commit()
    conn.close()
    return {"message": msg}


@router.get("/{character_id}", summary="리뷰 목록")
async def get_reviews(
        character_id: str,
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cr.id, cr.rating, cr.content, cr.created_at,
               u.username, u.profile_image_url, u.equipped_prefix, u.equipped_suffix
        FROM character_reviews cr
        JOIN users u ON cr.user_id = u.id
        WHERE cr.character_id = ?
        ORDER BY cr.created_at DESC
        LIMIT ? OFFSET ?
    """, (character_id, size, (page - 1) * size))
    rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as cnt FROM character_reviews WHERE character_id = ?",
                   (character_id,))
    total = cursor.fetchone()["cnt"]

    cursor.execute("SELECT AVG(rating) as avg FROM character_reviews WHERE character_id = ?",
                   (character_id,))
    avg = cursor.fetchone()["avg"]

    # 별점 분포
    cursor.execute("""
        SELECT rating, COUNT(*) as cnt
        FROM character_reviews WHERE character_id = ?
        GROUP BY rating ORDER BY rating DESC
    """, (character_id,))
    distribution = {str(r["rating"]): r["cnt"] for r in cursor.fetchall()}

    my_review = None
    if current_user:
        cursor.execute("""
            SELECT rating, content FROM character_reviews
            WHERE user_id = ? AND character_id = ?
        """, (current_user["id"], character_id))
        my_review = cursor.fetchone()
        if my_review:
            my_review = dict(my_review)

    conn.close()
    return {
        "total": total,
        "average": round(avg, 1) if avg else 0,
        "distribution": distribution,
        "my_review": my_review,
        "reviews": [dict(row) for row in rows],
    }


@router.delete("/{character_id}", summary="리뷰 삭제")
async def delete_review(
        character_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM character_reviews WHERE user_id = ? AND character_id = ?
    """, (current_user["id"], character_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")
    conn.commit()
    conn.close()
    return {"message": "리뷰 삭제 완료"}