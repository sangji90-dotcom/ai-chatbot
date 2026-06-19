from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from deps import get_current_user

router = APIRouter(
    prefix="/likes",
    tags=["좋아요"],
    responses={404: {"description": "찾을 수 없습니다"}}
)

@router.get("/me", summary="내 좋아요 목록", description="내가 좋아요한 캐릭터 목록을 반환합니다.")
async def get_my_likes(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.* FROM characters c
        JOIN character_likes cl ON c.id = cl.character_id
        WHERE cl.user_id = ?
        ORDER BY cl.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/{character_id}", summary="캐릭터 좋아요", description="캐릭터에 좋아요를 누릅니다.")
async def like_character(
        character_id: str,
        current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM characters WHERE id = ?", (character_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")

    try:
        cursor.execute("""
            INSERT INTO character_likes (user_id, character_id) VALUES (?, ?)
        """, (current_user["id"], character_id))
        cursor.execute("""
            UPDATE characters SET like_count = like_count + 1 WHERE id = ?
        """, (character_id,))
        conn.commit()
        conn.close()

        check_and_grant(current_user["id"], "first_like")

        return {"message": "좋아요 완료"}
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 좋아요한 캐릭터입니다.")

@router.delete("/{character_id}", summary="좋아요 취소", description="캐릭터 좋아요를 취소합니다.")
async def unlike_character(
        character_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM character_likes WHERE user_id = ? AND character_id = ?
    """, (current_user["id"], character_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="좋아요하지 않은 캐릭터입니다.")

    cursor.execute("""
        UPDATE characters SET like_count = like_count - 1 WHERE id = ?
    """, (character_id,))
    conn.commit()
    conn.close()
    return {"message": "좋아요 취소 완료"}

# ===== 북마크 =====
@router.post("/bookmarks/{character_id}", summary="북마크 추가")
async def add_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO character_bookmarks (user_id, character_id) VALUES (?, ?)",
            (current_user["id"], character_id)
        )
        db.commit()
        return {"message": "북마크 추가 완료", "bookmarked": True}
    except:
        raise HTTPException(400, "이미 북마크한 캐릭터입니다.")

@router.delete("/bookmarks/{character_id}", summary="북마크 취소")
async def remove_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute(
        "DELETE FROM character_bookmarks WHERE user_id = ? AND character_id = ?",
        (current_user["id"], character_id)
    )
    db.commit()
    return {"message": "북마크 취소 완료", "bookmarked": False}

@router.get("/bookmarks", summary="내 북마크 목록")
async def get_bookmarks(current_user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("""
        SELECT c.*, cb.created_at as bookmarked_at
        FROM character_bookmarks cb
        JOIN characters c ON cb.character_id = c.id
        WHERE cb.user_id = ?
        ORDER BY cb.created_at DESC
    """, (current_user["id"],)).fetchall()
    return [dict(r) for r in rows]

@router.get("/bookmarks/{character_id}/status", summary="북마크 여부 확인")
async def check_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    row = db.execute(
        "SELECT id FROM character_bookmarks WHERE user_id = ? AND character_id = ?",
        (current_user["id"], character_id)
    ).fetchone()
    return {"bookmarked": row is not None}
