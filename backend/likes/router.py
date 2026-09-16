import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from core.db import read_only, transaction
from core.serializers import public_character, visible_character_filter
from deps import assert_character_access, get_current_user

router = APIRouter(
    prefix="/likes",
    tags=["좋아요"],
    responses={404: {"description": "찾을 수 없습니다"}},
)


def _my_list(sql: str, params: tuple, user: dict) -> list[dict]:
    with read_only() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    # SELECT c.* 를 그대로 반환하면 캐릭터 prompt 까지 나간다
    return [public_character(r, user["id"]) for r in rows]


# ── 좋아요 ──────────────────────────────────────────────────────────────
@router.get("/me", summary="내 좋아요 목록")
def get_my_likes(current_user: dict = Depends(get_current_user)):
    return _my_list(
        f"""
        SELECT c.* FROM characters c
        JOIN character_likes cl ON c.id = cl.character_id
        WHERE cl.user_id = ?
          AND (c.user_id = ? OR {visible_character_filter(current_user)})
        ORDER BY cl.created_at DESC
        """,
        (current_user["id"], current_user["id"]),
        current_user,
    )


@router.post("/{character_id}", summary="캐릭터 좋아요")
def like_character(character_id: str, current_user: dict = Depends(get_current_user)):
    from achievements.router import check_and_grant

    # 접근 권한이 없는 캐릭터에는 좋아요를 남길 수 없다
    assert_character_access(character_id, current_user)

    try:
        with transaction() as cur:
            cur.execute(
                "INSERT INTO character_likes (user_id, character_id) VALUES (?, ?)",
                (current_user["id"], character_id),
            )
            cur.execute(
                "UPDATE characters SET like_count = like_count + 1 WHERE id = ?",
                (character_id,),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 좋아요한 캐릭터입니다.")

    check_and_grant(current_user["id"], "first_like")
    return {"message": "좋아요 완료"}


@router.delete("/{character_id}", summary="좋아요 취소")
def unlike_character(character_id: str, current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute(
            "DELETE FROM character_likes WHERE user_id = ? AND character_id = ?",
            (current_user["id"], character_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=400, detail="좋아요하지 않은 캐릭터입니다.")
        # 카운터가 음수로 내려가지 않게 하한을 건다
        cur.execute(
            "UPDATE characters SET like_count = MAX(0, like_count - 1) WHERE id = ?",
            (character_id,),
        )
    return {"message": "좋아요 취소 완료"}


# ── 북마크 ──────────────────────────────────────────────────────────────
# 기존 구현은 네 엔드포인트 모두 conn.close() 가 없어 커넥션이 샜고,
# 캐릭터 존재/권한 확인도 없었다.
@router.post("/bookmarks/{character_id}", summary="북마크 추가")
def add_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    assert_character_access(character_id, current_user)
    try:
        with transaction() as cur:
            cur.execute(
                "INSERT INTO character_bookmarks (user_id, character_id) VALUES (?, ?)",
                (current_user["id"], character_id),
            )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 북마크한 캐릭터입니다.")
    return {"message": "북마크 추가 완료", "bookmarked": True}


@router.delete("/bookmarks/{character_id}", summary="북마크 취소")
def remove_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute(
            "DELETE FROM character_bookmarks WHERE user_id = ? AND character_id = ?",
            (current_user["id"], character_id),
        )
    return {"message": "북마크 취소 완료", "bookmarked": False}


@router.get("/bookmarks", summary="내 북마크 목록")
def get_bookmarks(current_user: dict = Depends(get_current_user)):
    return _my_list(
        f"""
        SELECT c.*, cb.created_at AS bookmarked_at
        FROM character_bookmarks cb
        JOIN characters c ON cb.character_id = c.id
        WHERE cb.user_id = ?
          AND (c.user_id = ? OR {visible_character_filter(current_user)})
        ORDER BY cb.created_at DESC
        """,
        (current_user["id"], current_user["id"]),
        current_user,
    )


@router.get("/bookmarks/{character_id}/status", summary="북마크 여부 확인")
def check_bookmark(character_id: str, current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        cur.execute(
            "SELECT id FROM character_bookmarks WHERE user_id = ? AND character_id = ?",
            (current_user["id"], character_id),
        )
        return {"bookmarked": cur.fetchone() is not None}
