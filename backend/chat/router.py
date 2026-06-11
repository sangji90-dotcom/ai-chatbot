from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth.router import get_optional_user, get_current_user
from google import genai
import os
from dotenv import load_dotenv

router = APIRouter(prefix="/chat", tags=["대화"])
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat_histories = {}

OUTPUT_LENGTH = {
    "short": 300,
    "medium": 1000,
    "long": 2000
}

CHAT_DEDUCT = 50

class ChatRequest(BaseModel):
    character_id: str
    message: str
    session_id: str

class RatingRequest(BaseModel):
    session_id: str
    message_id: int
    rating: str

class OocRequest(BaseModel):
    session_id: str
    character_id: str
    message_id: int
    new_content: str

@router.post("", summary="대화하기", description="AI 캐릭터와 대화합니다. '요약!' 입력 시 대화 요약. 1회당 50토큰 차감.")
async def chat(
        request: ChatRequest,
        current_user: dict = Depends(get_optional_user)):
    from prompt import characters
    from tokens.router import deduct_token
    from achievements.router import check_and_grant

    all_characters = dict(characters)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE id = ?", (request.character_id,))
    row = cursor.fetchone()

    if row:
        all_characters[row["id"]] = {
            "name": row["name"],
            "prompt": row["prompt"]
        }
        cursor.execute("UPDATE characters SET chat_count = chat_count + 1 WHERE id = ?",
                       (request.character_id,))
        conn.commit()

    conn.close()

    if request.character_id not in all_characters:
        return {"error": "캐릭터를 찾을 수 없습니다"}

    character = all_characters[request.character_id]
    session_key = f"{request.session_id}_{request.character_id}"

    # 토큰 차감 + 출력량 설정 (로그인 유저만)
    max_tokens = 1000
    if current_user:
        deduct_token(current_user["id"], CHAT_DEDUCT, f"{character['name']}와 대화")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT output_length FROM users WHERE id = ?", (current_user["id"],))
        u = cursor.fetchone()
        conn.close()
        if u:
            max_tokens = OUTPUT_LENGTH.get(u["output_length"], 1000)

    # 이어하기 — 메모리에 없으면 DB에서 복원
    if session_key not in chat_histories:
        if current_user:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM chat_history
                WHERE session_id = ? AND character_id = ? AND user_id = ?
                ORDER BY created_at ASC
            """, (request.session_id, request.character_id, current_user["id"]))
            rows = cursor.fetchall()
            conn.close()
            chat_histories[session_key] = [
                {"role": r["role"], "content": r["content"]} for r in rows
            ]
        else:
            chat_histories[session_key] = []

    # 유저노트 + 페르소나 + 메모리북
    user_notes_text = ""
    if current_user:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT content FROM user_notes WHERE user_id = ? AND character_id = ? ORDER BY created_at ASC",
                       (current_user["id"], request.character_id))
        notes = cursor.fetchall()

        cursor.execute("SELECT name, content FROM user_personas WHERE user_id = ? AND character_id = ? ORDER BY created_at ASC",
                       (current_user["id"], request.character_id))
        personas = cursor.fetchall()

        cursor.execute("SELECT title, content FROM memory_book WHERE user_id = ? AND character_id = ? ORDER BY created_at ASC",
                       (current_user["id"], request.character_id))
        memories = cursor.fetchall()
        conn.close()

        if notes:
            user_notes_text += "\n\n[유저 기본 정보 — 자연스럽게 반영하되 직접 언급 금지]\n"
            user_notes_text += "\n".join([f"- {n['content']}" for n in notes])

        if personas:
            user_notes_text += "\n\n[유저 캐릭터 설정 — 롤플레잉에 적극 반영]\n"
            user_notes_text += "\n".join([
                f"- {p['name']}: {p['content']}" if p['name'] else f"- {p['content']}"
                for p in personas
            ])

        if memories:
            user_notes_text += "\n\n[중요 기억 — 반드시 기억하고 대화에 반영]\n"
            user_notes_text += "\n".join([
                f"- [{m['title']}] {m['content']}" if m['title'] else f"- {m['content']}"
                for m in memories
            ])

    system_instruction = character["prompt"] + user_notes_text
    history = chat_histories[session_key]

    # 요약 분기
    if request.message.strip() == "요약!":
        if len(history) < 4:
            return {"character": character["name"], "message": "아직 요약할 대화가 충분하지 않아요."}

        history_text = "\n".join([
            f"{'유저' if m['role'] == 'user' else character['name']}: {m['content']}"
            for m in history
        ])

        summary_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": history_text}]}],
            config={
                "system_instruction": "지금까지의 대화 내용을 간결하게 요약해줘. 중요한 사건, 감정, 결정만 남기고 압축해줘. 3~5문장으로.",
                "max_output_tokens": 500,
            }
        )

        summary = summary_response.text
        chat_histories[session_key] = [
            {"role": "user", "content": f"[이전 대화 요약]\n{summary}"},
            {"role": "assistant", "content": "네, 이전 내용을 기억하고 있어요. 계속 이야기해요."}
        ]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (session_id, character_id, user_id, role, content)
            VALUES (?, ?, ?, ?, ?)
        """, (request.session_id, request.character_id,
              current_user["id"] if current_user else None,
              "system", f"[요약]\n{summary}"))
        conn.commit()
        conn.close()

        return {"character": character["name"], "message": f"📝 대화를 요약했어요!\n\n{summary}"}

    # 일반 대화
    history.append({"role": "user", "content": request.message})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_history (session_id, character_id, user_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (request.session_id, request.character_id,
          current_user["id"] if current_user else None,
          "user", request.message))

    contents = []
    for msg in history[-30:]:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "system_instruction": system_instruction,
            "max_output_tokens": max_tokens,
        }
    )

    assistant_message = response.text
    history.append({"role": "assistant", "content": assistant_message})
    chat_histories[session_key] = history

    cursor.execute("""
        INSERT INTO chat_history (session_id, character_id, user_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (request.session_id, request.character_id,
          current_user["id"] if current_user else None,
          "assistant", assistant_message))
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()

    # 업적 체크 (로그인 유저만)
    if current_user:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM chat_history
            WHERE user_id = ? AND role = 'user'
        """, (current_user["id"],))
        total = cursor.fetchone()["cnt"]

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM chat_history
            WHERE user_id = ? AND character_id = ? AND role = 'user'
        """, (current_user["id"], request.character_id))
        single = cursor.fetchone()["cnt"]
        conn.close()

        if total == 1: check_and_grant(current_user["id"], "first_chat")
        if total == 10: check_and_grant(current_user["id"], "chat_10")
        if total == 50: check_and_grant(current_user["id"], "chat_50")
        if total == 100: check_and_grant(current_user["id"], "chat_100")
        if total == 500: check_and_grant(current_user["id"], "chat_500")
        if total == 1000: check_and_grant(current_user["id"], "chat_1000")
        if single == 10: check_and_grant(current_user["id"], "chat_single_10")
        if single == 50: check_and_grant(current_user["id"], "chat_single_50")
        if single == 100: check_and_grant(current_user["id"], "chat_single_100")

    return {
        "character": character["name"],
        "message": assistant_message,
        "message_id": message_id
    }

# ===== 메시지 평가 =====
@router.post("/rating", summary="메시지 평가", description="AI 응답에 좋아요/싫어요를 남깁니다.")
async def rate_message(
        request: RatingRequest,
        current_user: dict = Depends(get_current_user)):
    if request.rating not in ["like", "dislike"]:
        raise HTTPException(status_code=400, detail="rating은 like 또는 dislike만 가능합니다.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO message_ratings (user_id, session_id, message_id, rating)
        VALUES (?, ?, ?, ?)
    """, (current_user["id"], request.session_id, request.message_id, request.rating))
    conn.commit()
    conn.close()
    return {"message": "평가 완료"}

# ===== OOC 모드 =====
@router.patch("/ooc", summary="OOC 수정", description="AI 응답을 직접 수정합니다. (Out Of Character)")
async def ooc_edit(
        request: OocRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE chat_history SET content = ? WHERE id = ? AND user_id = ?
    """, (request.new_content, request.message_id, current_user["id"]))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    conn.commit()
    conn.close()

    session_key = f"{request.session_id}_{request.character_id}"
    if session_key in chat_histories:
        for msg in chat_histories[session_key]:
            if msg.get("id") == request.message_id:
                msg["content"] = request.new_content
                break

    return {"message": "메시지 수정 완료"}

# ===== 새 채팅 =====
@router.post("/new/{character_id}", summary="새 채팅 시작", description="현재 대화를 초기화하고 새로 시작합니다.")
async def new_chat(
        character_id: str,
        session_id: str,
        current_user: dict = Depends(get_optional_user)):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "새 채팅 시작 완료", "session_key": session_key}

# ===== 이어하기 =====
@router.get("/resume/{character_id}", summary="대화 이어하기", description="이전 대화를 불러와 이어갑니다.")
async def resume_chat(
        character_id: str,
        session_id: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, created_at FROM chat_history
        WHERE session_id = ? AND character_id = ? AND user_id = ?
        ORDER BY created_at ASC
    """, (session_id, character_id, current_user["id"]))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"history": [], "message": "이전 대화 없음"}

    session_key = f"{session_id}_{character_id}"
    chat_histories[session_key] = [
        {"role": r["role"], "content": r["content"]} for r in rows
    ]

    return {
        "history": [dict(r) for r in rows],
        "message": f"대화 {len(rows)}개 복원 완료"
    }

@router.get("/history/{character_id}", summary="대화 기록 조회", description="캐릭터와의 전체 대화 기록을 반환합니다.")
async def get_chat_history(
        character_id: str,
        current_user: dict = Depends(get_optional_user)):
    if not current_user:
        return []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, created_at FROM chat_history
        WHERE character_id = ? AND user_id = ?
        ORDER BY created_at ASC
    """, (character_id, current_user["id"]))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.delete("/{session_id}/{character_id}", summary="대화 초기화", description="해당 세션의 대화 기록을 삭제합니다.")
async def clear_chat(session_id: str, character_id: str):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "대화 기록 삭제 완료"}