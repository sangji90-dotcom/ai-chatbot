# 테이블 스키마 문서화용 (실제 생성은 database.py에서)

TABLES = {
    "users": ["id", "email", "username", "password", "created_at"],
    "characters": ["id", "user_id", "name", "description", "prompt",
                   "first_message", "situation", "category",
                   "visibility", "image_url", "chat_count", "created_at"],
    "chat_history": ["id", "session_id", "character_id", "user_id",
                     "role", "content", "created_at"],
    "user_notes": ["id", "user_id", "character_id", "content", "created_at"]
}