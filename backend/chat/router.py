from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from deps import get_current_user, get_optional_user
from google import genai
import os
import re
from dotenv import load_dotenv
import io
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
AUTO_SUMMARY_THRESHOLD = 100
RECENT_TURNS = 40
SEXUAL_KEYWORDS = ["로리", "쇼타", "loli", "shota", "어린이 성", "아동 성"]

TAG_INSTRUCTION = """
응답 마지막에 반드시 아래 형식으로 태그를 추가해줘. 태그는 대화 내용을 분석해서 결정해.

[EMOTION:태그] [SITUATION:태그]

감정 태그 옵션: neutral, happy, sad, angry, shy, surprised, love, embarrassed, crying, serious
상황 태그 옵션: default, indoor, outdoor, night, cafe, forest, rain, sunny, fantasy, dramatic

예시: [EMOTION:happy] [SITUATION:cafe]
"""


def check_harmful_content(message: str) -> bool:
    for keyword in SEXUAL_KEYWORDS:
        if keyword.lower() in message.lower():
            return True
    return False


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


async def auto_summarize(history: list, character_name: str) -> list:
    old_history = history[:-RECENT_TURNS]
    recent_history = history[-RECENT_TURNS:]

    history_text = "\n".join([
        f"{'유저' if m['role'] == 'user' else character_name}: {m['content']}"
        for m in old_history
    ])

    summary_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": history_text}]}],
        config={
            "system_instruction": """
이전 대화를 핵심만 추출해서 메모리 패스 형식으로 요약해줘.

형식:
[관계] 유저와 캐릭터의 현재 관계
[주요 사건] 중요한 사건 3개 이하
[감정 흐름] 현재 감정 상태
[약속/결정] 중요한 약속이나 결정사항
[기타 기억] 기억해야 할 세부 정보

5줄 이내로 간결하게.
""",
            "max_output_tokens": 300,
        }
    )

    summary = summary_response.text
    return [
        {"role": "user", "content": f"[메모리 패스 - 이전 대화 핵심 기억]\n{summary}"},
        {"role": "assistant", "content": "네, 이전 내용을 기억하고 있어요."},
        *recent_history
    ]


async def extract_memory(user_id: int, character_id: str, message: str, response: str, character_name: str):
    extract_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": f"유저: {message}\n{character_name}: {response}"}]}],
        config={
            "system_instruction": """
이 대화에서 나중에 기억해야 할 중요한 정보가 있으면 한 줄로 추출해줘.
중요한 정보: 유저의 이름, 관계 변화, 중요한 약속, 감정적으로 중요한 사건
없으면 "없음"이라고만 답해줘.
절대 설명하지 말고 한 줄만.
""",
            "max_output_tokens": 100,
        }
    )
    extracted = extract_response.text.strip()
    if extracted and extracted != "없음":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory_book (user_id, character_id, title, content)
            VALUES (?, ?, ?, ?)
        """, (user_id, character_id, "자동추출", extracted))
        conn.commit()
        conn.close()


@router.post("", summary="대화하기")
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

    # 토큰 차감 + 출력량 설정
    max_tokens = 1000
    if current_user:
        deduct_token(current_user["id"], CHAT_DEDUCT, f"{character['name']}와 대화")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT output_length, output_multiplier FROM users WHERE id = ?", (current_user["id"],))
        u = cursor.fetchone()
        conn.close()
        if u:
            base_tokens = OUTPUT_LENGTH.get(u["output_length"], 1000)
            multiplier = u["output_multiplier"] if u["output_multiplier"] else 1.0
            max_tokens = int(base_tokens * multiplier)

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

        if current_user:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_history (session_id, character_id, user_id, role, content)
                VALUES (?, ?, ?, ?, ?)
            """, (request.session_id, request.character_id,
                  current_user["id"], "system", f"[요약]\n{summary}"))
            conn.commit()
            conn.close()

        return {"character": character["name"], "message": f"📝 대화를 요약했어요!\n\n{summary}"}

    # 유해 콘텐츠 체크
    if check_harmful_content(request.message):
        return {
            "character": character["name"],
            "message": "해당 내용은 생성할 수 없어요."
        }

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
    conn.commit()

    # 100턴 초과 시 자동 요약
    if len(history) > AUTO_SUMMARY_THRESHOLD:
        history = await auto_summarize(history, character["name"])
        chat_histories[session_key] = history

    contents = []
    for msg in history:
        contents.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "system_instruction": system_instruction + TAG_INSTRUCTION,
            "max_output_tokens": max_tokens,
        }
    )

    raw_message = response.text

    # MAX_TOKENS로 잘린 경우 자동으로 이어서 생성 (최대 1회)
    MAX_CONTINUATIONS = 1
    continuation_count = 0

    while (
        response.candidates and
        response.candidates[0].finish_reason.name == "MAX_TOKENS" and
        continuation_count < MAX_CONTINUATIONS
    ):
        continuation_count += 1
        continuation_contents = contents + [
            {"role": "model", "parts": [{"text": raw_message}]},
            {"role": "user", "parts": [{"text": "(이어서 작성)"}]},
        ]
        continuation_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=continuation_contents,
            config={
                "system_instruction": system_instruction + TAG_INSTRUCTION,
                "max_output_tokens": max_tokens,
            }
        )
        raw_message += continuation_response.text
        response = continuation_response

    # 태그 추출
    emotion = "neutral"
    situation = "default"

    emotion_match = re.search(r'\[EMOTION:(\w+)\]', raw_message)
    situation_match = re.search(r'\[SITUATION:(\w+)\]', raw_message)

    if emotion_match:
        emotion = emotion_match.group(1)
    if situation_match:
        situation = situation_match.group(1)

    # 태그 제거한 순수 메시지
    assistant_message = re.sub(r'\[EMOTION:\w+\]\s*|\[SITUATION:\w+\]\s*', '', raw_message).strip()

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

    # 10턴마다 중요 정보 자동 추출 (메모리 패스 유저만)
    if current_user and len(history) % 10 == 0:
        from datetime import datetime
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT memory_pass_expires_at FROM users WHERE id = ?",
                       (current_user["id"],))
        u = cursor.fetchone()
        conn.close()

        has_pass = False
        if u and u["memory_pass_expires_at"]:
            try:
                expires = datetime.fromisoformat(u["memory_pass_expires_at"])
                has_pass = expires > datetime.now()
            except:
                pass

        if has_pass:
            await extract_memory(
                current_user["id"],
                request.character_id,
                request.message,
                assistant_message,
                character["name"]
            )

    # 업적 체크
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
        "message_id": message_id,
        "emotion": emotion,
        "situation": situation,
    }


@router.post("/rating", summary="메시지 평가")
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


@router.patch("/ooc", summary="OOC 수정")
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


@router.post("/new/{character_id}", summary="새 채팅 시작")
async def new_chat(
        character_id: str,
        session_id: str,
        current_user: dict = Depends(get_optional_user)):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "새 채팅 시작 완료", "session_key": session_key}


@router.get("/resume/{character_id}", summary="대화 이어하기")
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


@router.get("/history/{character_id}", summary="대화 기록 조회")
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


@router.delete("/{session_id}/{character_id}", summary="대화 초기화")
async def clear_chat(session_id: str, character_id: str):
    session_key = f"{session_id}_{character_id}"
    if session_key in chat_histories:
        del chat_histories[session_key]
    return {"message": "대화 기록 삭제 완료"}


@router.get("/export/{character_id}", summary="대화 PDF 내보내기")
async def export_chat_pdf(
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

    cursor.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
    char = cursor.fetchone()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="대화 기록이 없습니다.")

    char_name = char["name"] if char else character_id

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_name = "Helvetica"
    font_path = "NanumGothic-Regular.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
        font_name = "NanumGothic"

    c.setFont(font_name, 16)
    c.drawString(50, height - 50, f"{char_name}와의 대화")
    c.setFont(font_name, 9)
    c.drawString(50, height - 70, f"세션: {session_id}  |  총 {len(rows)}개 메시지")

    y = height - 100
    line_height = 16
    margin = 50
    max_width = width - margin * 2

    def draw_text_block(c, text, x, y, font_name, font_size, max_width):
        lines = []
        for paragraph in text.split('\n'):
            line = ""
            for char in paragraph:
                test_line = line + char
                if c.stringWidth(test_line, font_name, font_size) > max_width:
                    lines.append(line)
                    line = char
                else:
                    line = test_line
            lines.append(line)
        return lines

    for row in rows:
        role = row["role"]
        content = row["content"]
        created_at = row["created_at"]

        if role == "system":
            continue

        label = "나" if role == "user" else char_name
        color = (0.1, 0.4, 0.8) if role == "user" else (0.1, 0.6, 0.3)

        if y < 100:
            c.showPage()
            y = height - 50

        c.setFillColorRGB(*color)
        c.setFont(font_name, 10)
        c.drawString(margin, y, f"[{label}]  {created_at[:16]}")
        y -= line_height

        c.setFillColorRGB(0, 0, 0)
        lines = draw_text_block(c, content, margin, y, font_name, 9, max_width)
        for line in lines:
            if y < 60:
                c.showPage()
                y = height - 50
            c.drawString(margin + 10, y, line)
            y -= line_height

        y -= 8

    c.save()
    buffer.seek(0)

    filename = f"{char_name}_대화_{session_id[:8]}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )