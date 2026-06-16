from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from database import get_db
from deps import get_current_user, get_optional_user
from typing import Optional
import uuid
import os


router = APIRouter(prefix="/users", tags=["유저"])


class NoteRequest(BaseModel):
    character_id: str
    content: str

class PersonaRequest(BaseModel):
    character_id: str
    name: str = ""
    content: str

class MemoryBookRequest(BaseModel):
    character_id: str
    title: str = ""
    content: str

class SettingsRequest(BaseModel):
    safety_mode: int = None
    output_length: str = None
    output_multiplier: float = None
    image_mode_chat: int = None
    image_mode_bg: int = None
    image_mode_bottom: int = None
    image_mode_multi: int = None

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ===== 내 캐릭터 목록 =====
@router.get("/me/characters", summary="내 캐릭터 목록")
async def get_my_characters(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE user_id = ? ORDER BY created_at DESC",
                   (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== 최근 대화한 캐릭터 =====
@router.get("/me/recent-chats", summary="최근 대화 캐릭터")
async def get_recent_chats(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ch.character_id, MAX(ch.created_at) as last_chat,
               c.name, c.image_url, c.description
        FROM chat_history ch
        LEFT JOIN characters c ON ch.character_id = c.id
        WHERE ch.user_id = ?
        GROUP BY ch.character_id
        ORDER BY last_chat DESC
        LIMIT 10
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== 설정 조회 =====
@router.get("/me/settings", summary="내 설정 조회")
async def get_settings(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT safety_mode, output_length, output_multiplier,
               image_mode_chat, image_mode_bg,
               image_mode_bottom, image_mode_multi
        FROM users WHERE id = ?
    """, (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


# ===== 설정 변경 =====
@router.patch("/me/settings", summary="내 설정 변경")
async def update_settings(
        request: SettingsRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    fields = []
    values = []

    if request.safety_mode is not None:
        fields.append("safety_mode = ?"); values.append(request.safety_mode)
    if request.output_length is not None:
        fields.append("output_length = ?"); values.append(request.output_length)
    if request.output_multiplier is not None:
        if request.output_multiplier not in [1.0, 1.25, 1.5, 2.0, 3.0, 4.0]:
            conn.close()
            raise HTTPException(status_code=400, detail="유효하지 않은 배율입니다.")
        fields.append("output_multiplier = ?"); values.append(request.output_multiplier)
    if request.image_mode_chat is not None:
        fields.append("image_mode_chat = ?"); values.append(request.image_mode_chat)
    if request.image_mode_bg is not None:
        fields.append("image_mode_bg = ?"); values.append(request.image_mode_bg)
    if request.image_mode_bottom is not None:
        fields.append("image_mode_bottom = ?"); values.append(request.image_mode_bottom)
    if request.image_mode_multi is not None:
        fields.append("image_mode_multi = ?"); values.append(request.image_mode_multi)

    if fields:
        values.append(current_user["id"])
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return {"message": "설정 변경 완료"}


# ===== 유저노트 CRUD =====
@router.post("/me/notes", summary="노트 저장")
async def create_note(request: NoteRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_notes (user_id, character_id, content) VALUES (?, ?, ?)",
                   (current_user["id"], request.character_id, request.content))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return {"id": note_id, "message": "노트 저장 완료"}


@router.get("/me/notes/{character_id}", summary="노트 조회")
async def get_notes(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_notes WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/me/notes/{note_id}", summary="노트 수정")
async def update_note(note_id: int, request: NoteRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 노트만 수정 가능합니다.")
    cursor.execute("UPDATE user_notes SET content = ? WHERE id = ?", (request.content, note_id))
    conn.commit()
    conn.close()
    return {"message": "노트 수정 완료"}


@router.delete("/me/notes/{note_id}", summary="노트 삭제")
async def delete_note(note_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 노트만 삭제 가능합니다.")
    cursor.execute("DELETE FROM user_notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"message": "노트 삭제 완료"}


# ===== 페르소나 CRUD =====
@router.post("/me/personas", summary="페르소나 저장")
async def create_persona(request: PersonaRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_personas (user_id, character_id, name, content) VALUES (?, ?, ?, ?)",
                   (current_user["id"], request.character_id, request.name, request.content))
    conn.commit()
    persona_id = cursor.lastrowid
    conn.close()
    return {"id": persona_id, "message": "페르소나 저장 완료"}


@router.get("/me/personas/{character_id}", summary="페르소나 조회")
async def get_personas(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_personas WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/me/personas/{persona_id}", summary="페르소나 수정")
async def update_persona(persona_id: int, request: PersonaRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 페르소나만 수정 가능합니다.")
    cursor.execute("UPDATE user_personas SET name = ?, content = ? WHERE id = ?",
                   (request.name, request.content, persona_id))
    conn.commit()
    conn.close()
    return {"message": "페르소나 수정 완료"}


@router.delete("/me/personas/{persona_id}", summary="페르소나 삭제")
async def delete_persona(persona_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="페르소나를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 페르소나만 삭제 가능합니다.")
    cursor.execute("DELETE FROM user_personas WHERE id = ?", (persona_id,))
    conn.commit()
    conn.close()
    return {"message": "페르소나 삭제 완료"}


# ===== 메모리북 CRUD =====
@router.post("/me/memory-book", summary="메모리북 저장")
async def create_memory(request: MemoryBookRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory_book (user_id, character_id, title, content) VALUES (?, ?, ?, ?)",
                   (current_user["id"], request.character_id, request.title, request.content))
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()
    return {"id": memory_id, "message": "메모리북 저장 완료"}


@router.get("/me/memory-book/{character_id}", summary="메모리북 조회")
async def get_memory_book(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_book WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.delete("/me/memory-book/{memory_id}", summary="메모리북 삭제")
async def delete_memory(memory_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM memory_book WHERE id = ?", (memory_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="메모리를 찾을 수 없습니다.")
    if row["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="본인 메모리만 삭제 가능합니다.")
    cursor.execute("DELETE FROM memory_book WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()
    return {"message": "메모리북 삭제 완료"}


# ===== 차단 목록 =====
@router.get("/me/blocks", summary="차단 목록")
async def get_block_list(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, ub.created_at as blocked_at
        FROM user_blocks ub
        JOIN users u ON ub.blocked_id = u.id
        WHERE ub.blocker_id = ?
        ORDER BY ub.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ===== 내 정보 조회 =====
@router.get("/me", summary="내 정보 조회")
async def get_me(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, username, is_adult, safety_mode,
               token_balance, token_purchased, token_event,
               attendance_streak, last_attendance_date, created_at
        FROM users WHERE id = ?
    """, (current_user["id"],))
    user = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as cnt FROM characters WHERE user_id = ?",
                   (current_user["id"],))
    char_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?",
                   (current_user["id"],))
    follower_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE follower_id = ?",
                   (current_user["id"],))
    following_count = cursor.fetchone()["cnt"]

    conn.close()
    return {
        **dict(user),
        "character_count": char_count,
        "follower_count": follower_count,
        "following_count": following_count
    }


# ===== 내 정보 수정 =====
@router.patch("/me", summary="내 정보 수정")
async def update_profile(
        request: UpdateProfileRequest,
        current_user: dict = Depends(get_current_user)):
    if not request.username:
        raise HTTPException(status_code=400, detail="변경할 정보가 없습니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username = ? WHERE id = ?",
                   (request.username, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "프로필 수정 완료"}

@router.post("/me/profile-image", summary="프로필 이미지 업로드")
async def upload_profile_image(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)):

    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 5MB 이하여야 합니다.")

    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_dir = "../frontend/images/profiles"
    os.makedirs(save_dir, exist_ok=True)

    with open(f"{save_dir}/{filename}", "wb") as f:
        f.write(contents)

    image_url = f"/images/profiles/{filename}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_image_url = ? WHERE id = ?",
                   (image_url, current_user["id"]))
    conn.commit()
    conn.close()

    return {"image_url": image_url, "message": "프로필 이미지 업로드 완료"}


# ===== 비밀번호 변경 =====
@router.patch("/me/password", summary="비밀번호 변경")
async def change_password(
        request: ChangePasswordRequest,
        current_user: dict = Depends(get_current_user)):
    import bcrypt

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE id = ?", (current_user["id"],))
    user = cursor.fetchone()

    if not bcrypt.checkpw(request.current_password.encode('utf-8'),
                          user["password"].encode('utf-8')):
        conn.close()
        raise HTTPException(status_code=400, detail="현재 비밀번호가 틀렸습니다.")

    new_hashed = bcrypt.hashpw(request.new_password.encode('utf-8'),
                               bcrypt.gensalt()).decode('utf-8')
    cursor.execute("UPDATE users SET password = ? WHERE id = ?",
                   (new_hashed, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "비밀번호 변경 완료"}


# ===== 회원 탈퇴 =====
@router.delete("/me", summary="회원 탈퇴")
async def delete_account(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_notes WHERE user_id = ?", (current_user["id"],))
    cursor.execute("DELETE FROM user_personas WHERE user_id = ?", (current_user["id"],))
    cursor.execute("DELETE FROM memory_book WHERE user_id = ?", (current_user["id"],))
    cursor.execute("DELETE FROM character_likes WHERE user_id = ?", (current_user["id"],))
    cursor.execute("DELETE FROM follows WHERE follower_id = ? OR following_id = ?",
                   (current_user["id"], current_user["id"]))
    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (current_user["id"],))
    cursor.execute("DELETE FROM token_history WHERE user_id = ?", (current_user["id"],))
    cursor.execute("UPDATE characters SET visibility = 'private' WHERE user_id = ?",
                   (current_user["id"],))
    cursor.execute("DELETE FROM users WHERE id = ?", (current_user["id"],))
    conn.commit()
    conn.close()
    return {"message": "회원 탈퇴 완료"}


# ===== 유저 검색 =====
@router.get("/search", summary="유저 검색")
async def search_users(
        q: str,
        page: int = 1,
        size: int = 20,
        current_user: Optional[dict] = Depends(get_optional_user)):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.username, u.created_at,
               COUNT(DISTINCT c.id) as character_count,
               COUNT(DISTINCT f.follower_id) as follower_count
        FROM users u
        LEFT JOIN characters c ON c.user_id = u.id AND c.visibility = 'public'
        LEFT JOIN follows f ON f.following_id = u.id
        WHERE u.username LIKE ?
        GROUP BY u.id
        ORDER BY follower_count DESC
        LIMIT ? OFFSET ?
    """, (f"%{q}%", size, (page - 1) * size))
    users = cursor.fetchall()

    result = []
    for user in users:
        is_following = False
        if current_user:
            cursor.execute("SELECT id FROM follows WHERE follower_id = ? AND following_id = ?",
                           (current_user["id"], user["id"]))
            is_following = cursor.fetchone() is not None

        cursor.execute("""
            SELECT id, name, description, image_url, chat_count, like_count
            FROM characters
            WHERE user_id = ? AND visibility = 'public'
            ORDER BY created_at DESC LIMIT 3
        """, (user["id"],))
        recent_characters = cursor.fetchall()

        result.append({
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
            "character_count": user["character_count"],
            "follower_count": user["follower_count"],
            "is_following": is_following,
            "recent_characters": [dict(c) for c in recent_characters]
        })

    conn.close()
    return result


# ===== 차단 =====
@router.post("/{user_id}/block", summary="유저 차단")
async def block_user(
        user_id: int,
        current_user: dict = Depends(get_current_user)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="본인을 차단할 수 없습니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    try:
        cursor.execute("INSERT INTO user_blocks (blocker_id, blocked_id) VALUES (?, ?)",
                       (current_user["id"], user_id))
        cursor.execute("""
            DELETE FROM follows WHERE
            (follower_id = ? AND following_id = ?) OR
            (follower_id = ? AND following_id = ?)
        """, (current_user["id"], user_id, user_id, current_user["id"]))
        conn.commit()
        conn.close()
        return {"message": "차단 완료"}
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 차단한 사용자입니다.")


# ===== 차단 해제 =====
@router.delete("/{user_id}/block", summary="차단 해제")
async def unblock_user(
        user_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?",
                   (current_user["id"], user_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="차단하지 않은 사용자입니다.")
    conn.commit()
    conn.close()
    return {"message": "차단 해제 완료"}


# ===== 유저 공개 프로필 =====
@router.get("/{user_id}", summary="유저 공개 프로필")
async def get_user_profile(
        user_id: int,
        current_user: dict = Depends(get_optional_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    cursor.execute("SELECT COUNT(*) as cnt FROM characters WHERE user_id = ? AND visibility = 'public'",
                   (user_id,))
    char_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (user_id,))
    follower_count = cursor.fetchone()["cnt"]

    is_following = False
    if current_user:
        cursor.execute("SELECT id FROM follows WHERE follower_id = ? AND following_id = ?",
                       (current_user["id"], user_id))
        is_following = cursor.fetchone() is not None

    conn.close()
    return {
        "id": dict(user)["id"],
        "username": dict(user)["username"],
        "created_at": dict(user)["created_at"],
        "character_count": char_count,
        "follower_count": follower_count,
        "is_following": is_following
    }