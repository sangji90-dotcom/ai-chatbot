from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from deps import get_current_user
from typing import Optional, List

router = APIRouter(
    prefix="/follows",
    tags=["팔로우"],
    responses={404: {"description": "찾을 수 없습니다"}}
)


@router.get("/me/followers", summary="내 팔로워 목록")
async def get_my_followers(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, f.created_at as followed_at
        FROM follows f
        JOIN users u ON f.follower_id = u.id
        WHERE f.following_id = ?
        ORDER BY f.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/{user_id}", summary="팔로우", description="창작자를 팔로우합니다.")
async def follow_user(
        user_id: int,
        current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="본인을 팔로우할 수 없습니다.")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    try:
        cursor.execute("""
            INSERT INTO follows (follower_id, following_id) VALUES (?, ?)
        """, (current_user["id"], user_id))
        conn.commit()

        # 팔로워 수 체크
        cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (user_id,))
        follower_count = cursor.fetchone()["cnt"]
        conn.close()

        # 팔로우한 사람 업적
        check_and_grant(current_user["id"], "first_follow")

        # 팔로워 받은 사람 업적
        if follower_count == 1: check_and_grant(user_id, "first_follower")
        if follower_count == 10: check_and_grant(user_id, "follower_10")
        if follower_count == 50: check_and_grant(user_id, "follower_50")
        if follower_count == 100: check_and_grant(user_id, "follower_100")

        return {"message": "팔로우 완료"}
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 팔로우한 사용자입니다.")

@router.delete("/{user_id}", summary="언팔로우", description="팔로우를 취소합니다.")
async def unfollow_user(
        user_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM follows WHERE follower_id = ? AND following_id = ?
    """, (current_user["id"], user_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="팔로우하지 않은 사용자입니다.")

    conn.commit()
    conn.close()
    return {"message": "언팔로우 완료"}

@router.get("/me", summary="내 팔로우 목록", description="내가 팔로우한 창작자 목록을 반환합니다.")
async def get_my_follows(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.created_at FROM users u
        JOIN follows f ON u.id = f.following_id
        WHERE f.follower_id = ?
        ORDER BY f.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/me/new-characters", summary="팔로우한 창작자의 새 캐릭터", description="팔로우한 창작자가 최근 등록한 캐릭터 목록을 반환합니다.")
async def get_following_new_characters(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.username as creator FROM characters c
        JOIN users u ON c.user_id = u.id
        JOIN follows f ON c.user_id = f.following_id
        WHERE f.follower_id = ?
        ORDER BY c.created_at DESC
        LIMIT 20
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]