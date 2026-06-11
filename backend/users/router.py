from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth.router import get_current_user

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
    image_mode_chat: int = None
    image_mode_bg: int = None
    image_mode_bottom: int = None
    image_mode_multi: int = None

# ===== 내 캐릭터 목록 =====
@router.get("/me/characters", summary="내 캐릭터 목록", description="내가 생성한 캐릭터 목록을 반환합니다.")
async def get_my_characters(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE user_id = ? ORDER BY created_at DESC",
                   (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ===== 최근 대화한 캐릭터 =====
@router.get("/me/recent-chats", summary="최근 대화 캐릭터", description="최근 대화한 캐릭터 목록을 반환합니다.")
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

# ===== 설정 =====
@router.get("/me/settings", summary="내 설정 조회", description="세이프티 모드, 이미지 설정, 출력량 설정을 반환합니다.")
async def get_settings(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT safety_mode, output_length,
               image_mode_chat, image_mode_bg,
               image_mode_bottom, image_mode_multi
        FROM users WHERE id = ?
    """, (current_user["id"],))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@router.patch("/me/settings", summary="내 설정 변경", description="세이프티 모드, 이미지 설정, 출력량 설정을 변경합니다.")
async def update_settings(
        request: SettingsRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    fields = []
    values = []
    if request.safety_mode is not None:
        fields.append("safety_mode = ?")
        values.append(request.safety_mode)
    if request.output_length is not None:
        fields.append("output_length = ?")
        values.append(request.output_length)
    if request.image_mode_chat is not None:
        fields.append("image_mode_chat = ?")
        values.append(request.image_mode_chat)
    if request.image_mode_bg is not None:
        fields.append("image_mode_bg = ?")
        values.append(request.image_mode_bg)
    if request.image_mode_bottom is not None:
        fields.append("image_mode_bottom = ?")
        values.append(request.image_mode_bottom)
    if request.image_mode_multi is not None:
        fields.append("image_mode_multi = ?")
        values.append(request.image_mode_multi)

    if fields:
        values.append(current_user["id"])
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return {"message": "설정 변경 완료"}

# ===== 유저노트 CRUD =====
@router.post("/me/notes", summary="노트 저장", description="캐릭터에 대한 노트를 저장합니다.")
async def create_note(request: NoteRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_notes (user_id, character_id, content) VALUES (?, ?, ?)",
                   (current_user["id"], request.character_id, request.content))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return {"id": note_id, "message": "노트 저장 완료"}

@router.get("/me/notes/{character_id}", summary="노트 조회", description="캐릭터에 대한 노트 목록을 반환합니다.")
async def get_notes(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_notes WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.patch("/me/notes/{note_id}", summary="노트 수정", description="노트를 수정합니다.")
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

@router.delete("/me/notes/{note_id}", summary="노트 삭제", description="노트를 삭제합니다.")
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
@router.post("/me/personas", summary="페르소나 저장", description="캐릭터 롤플레잉용 페르소나를 저장합니다.")
async def create_persona(request: PersonaRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_personas (user_id, character_id, name, content) VALUES (?, ?, ?, ?)",
                   (current_user["id"], request.character_id, request.name, request.content))
    conn.commit()
    persona_id = cursor.lastrowid
    conn.close()
    return {"id": persona_id, "message": "페르소나 저장 완료"}

@router.get("/me/personas/{character_id}", summary="페르소나 조회", description="캐릭터 페르소나 목록을 반환합니다.")
async def get_personas(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_personas WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.patch("/me/personas/{persona_id}", summary="페르소나 수정", description="페르소나를 수정합니다.")
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

@router.delete("/me/personas/{persona_id}", summary="페르소나 삭제", description="페르소나를 삭제합니다.")
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
@router.post("/me/memory-book", summary="메모리북 저장", description="중요 기억을 메모리북에 저장합니다.")
async def create_memory(request: MemoryBookRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory_book (user_id, character_id, title, content) VALUES (?, ?, ?, ?)",
                   (current_user["id"], request.character_id, request.title, request.content))
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()
    return {"id": memory_id, "message": "메모리북 저장 완료"}

@router.get("/me/memory-book/{character_id}", summary="메모리북 조회", description="캐릭터 메모리북 목록을 반환합니다.")
async def get_memory_book(character_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memory_book WHERE user_id = ? AND character_id = ? ORDER BY created_at DESC",
                   (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.delete("/me/memory-book/{memory_id}", summary="메모리북 삭제", description="메모리북 항목을 삭제합니다.")
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