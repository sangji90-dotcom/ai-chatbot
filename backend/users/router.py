from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth.router import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

class NoteRequest(BaseModel):
    character_id: str
    content: str

# ===== 내 캐릭터 목록 =====
@router.get("/me/characters")
async def get_my_characters(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM characters WHERE user_id = ? ORDER BY created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ===== 최근 대화한 캐릭터 =====
@router.get("/me/recent-chats")
async def get_recent_chats(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT character_id,
               MAX(created_at) as last_chat
        FROM chat_history
        WHERE user_id = ?
        GROUP BY character_id
        ORDER BY last_chat DESC
        LIMIT 10
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ===== 유저노트 생성 =====
@router.post("/me/notes")
async def create_note(
        request: NoteRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_notes (user_id, character_id, content)
        VALUES (?, ?, ?)
    """, (current_user["id"], request.character_id, request.content))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    return {"id": note_id, "message": "노트 저장 완료"}

# ===== 유저노트 조회 =====
@router.get("/me/notes/{character_id}")
async def get_notes(
        character_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_notes
        WHERE user_id = ? AND character_id = ?
        ORDER BY created_at DESC
    """, (current_user["id"], character_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ===== 유저노트 수정 =====
@router.patch("/me/notes/{note_id}")
async def update_note(
        note_id: int,
        request: NoteRequest,
        current_user: dict = Depends(get_current_user)):
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

    cursor.execute("""
        UPDATE user_notes SET content = ? WHERE id = ?
    """, (request.content, note_id))
    conn.commit()
    conn.close()
    return {"message": "노트 수정 완료"}

# ===== 유저노트 삭제 =====
@router.delete("/me/notes/{note_id}")
async def delete_note(
        note_id: int,
        current_user: dict = Depends(get_current_user)):
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