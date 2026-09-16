"""응답 직렬화.

여러 라우터가 `SELECT c.*` 를 그대로 반환하면서 캐릭터의 `prompt` 컬럼까지 내보내고
있었다. prompt 는 제작자가 만든 핵심 자산이라 소유자 외에는 노출하면 안 된다.
"""

PUBLIC_CHARACTER_FIELDS = (
    "id", "user_id", "name", "description", "first_message", "situation",
    "visibility", "is_adult", "image_url", "chat_count", "like_count",
    "view_count", "party_enabled", "category", "likes", "dislikes", "created_at",
)


def public_character(row, viewer_id: int | None = None) -> dict:
    """소유자가 아니면 prompt 를 제거한 캐릭터 dict 를 만든다."""
    keys = row.keys() if hasattr(row, "keys") else row
    data = {k: row[k] for k in keys if k in PUBLIC_CHARACTER_FIELDS}
    data["is_adult"] = bool(data.get("is_adult", 0))
    data["party_enabled"] = bool(data.get("party_enabled", 0))
    if viewer_id is not None and row["user_id"] == viewer_id and "prompt" in keys:
        data["prompt"] = row["prompt"]
    if "tags" in keys:
        data["tags"] = row["tags"].split(",") if row["tags"] else []
    return data


def not_blocked_sql(user: dict | None, user_col: str) -> str:
    """차단한 상대의 콘텐츠를 제외하는 SQL 조각.

    user_blocks 테이블은 넣고 빼고 목록만 보여줄 뿐,
    어떤 목록 쿼리에서도 필터링에 쓰이지 않았다 — 차단해도 상대 글이 그대로 보였다.
    """
    if not user:
        return "1=1"
    uid = int(user["id"])
    return (
        f"({user_col} IS NULL OR {user_col} NOT IN ("
        f"  SELECT blocked_id FROM user_blocks WHERE blocker_id = {uid}"
        f"))"
    )


def visible_character_filter(user: dict | None, alias: str = "c") -> str:
    """목록 쿼리에 붙일 공개/성인 필터 SQL 조각."""
    parts = [f"{alias}.visibility = 'public'"]
    if not (user and user.get("is_adult")):
        parts.append(f"{alias}.is_adult = 0")
    return " AND ".join(parts)
