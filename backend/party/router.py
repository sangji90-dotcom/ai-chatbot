from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth.router import get_current_user
from google import genai
from dotenv import load_dotenv
import os
import json
import random
import string

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/party", tags=["파티챗"])

# 방별 WebSocket 연결 관리 {room_code: [(websocket, user_id, username)]}
room_connections: dict[str, list[tuple]] = {}

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class CreateRoomRequest(BaseModel):
    story_id: int
    max_members: int = 4

class JoinRoomRequest(BaseModel):
    code: str
    character_stats: dict

class CreateStoryRequest(BaseModel):
    title: str
    genre: str = "기타"
    background: str
    system_prompt: str
    image_url: str = ""

# ===== 스토리 =====

@router.get("/stories", summary="스토리 목록", description="전체 스토리 목록을 반환합니다.")
async def get_stories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories ORDER BY is_official DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/stories", summary="스토리 생성", description="새 스토리를 생성합니다.")
async def create_story(
        request: CreateStoryRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stories (user_id, title, genre, background, system_prompt, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        current_user["id"], request.title, request.genre,
        request.background, request.system_prompt, request.image_url
    ))
    conn.commit()
    story_id = cursor.lastrowid
    conn.close()
    return {"id": story_id, "message": "스토리 생성 완료"}

# ===== 방 생성/참여 =====

@router.post("/rooms", summary="파티방 생성", description="새 파티방을 생성합니다.")
async def create_room(
        request: CreateRoomRequest,
        current_user: dict = Depends(get_current_user)):
    code = generate_room_code()
    conn = get_db()
    cursor = conn.cursor()

    while True:
        cursor.execute("SELECT id FROM party_rooms WHERE code = ?", (code,))
        if not cursor.fetchone():
            break
        code = generate_room_code()

    cursor.execute("""
        INSERT INTO party_rooms (code, story_id, host_id, max_members)
        VALUES (?, ?, ?, ?)
    """, (code, request.story_id, current_user["id"], request.max_members))
    conn.commit()
    room_id = cursor.lastrowid
    conn.close()
    return {"room_id": room_id, "code": code, "message": "방 생성 완료"}

@router.post("/rooms/join", summary="파티방 참여", description="코드로 파티방에 참여합니다.")
async def join_room(
        request: JoinRoomRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (request.code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")
    if room["status"] != "waiting":
        conn.close()
        raise HTTPException(status_code=400, detail="이미 시작된 방입니다.")

    cursor.execute("SELECT COUNT(*) as cnt FROM party_members WHERE room_id = ?", (room["id"],))
    count = cursor.fetchone()["cnt"]
    if count >= room["max_members"]:
        conn.close()
        raise HTTPException(status_code=400, detail="방이 꽉 찼습니다.")

    cursor.execute("SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
                   (room["id"], current_user["id"]))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="이미 참여 중인 방입니다.")

    cursor.execute("""
        INSERT INTO party_members (room_id, user_id, character_stats)
        VALUES (?, ?, ?)
    """, (room["id"], current_user["id"],
          json.dumps(request.character_stats, ensure_ascii=False)))
    conn.commit()
    conn.close()
    return {"room_id": room["id"], "message": "방 참여 완료"}

@router.get("/rooms/{code}", summary="파티방 정보", description="파티방 정보와 참여자 목록을 반환합니다.")
async def get_room_info(code: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")

    cursor.execute("""
        SELECT pm.*, u.username FROM party_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.room_id = ?
    """, (room["id"],))
    members = cursor.fetchall()
    conn.close()

    return {
        "room": dict(room),
        "members": [dict(m) for m in members]
    }

# ===== WebSocket =====

@router.websocket("/ws/{room_code}/{user_id}")
async def party_websocket(websocket: WebSocket, room_code: str, user_id: int):
    await websocket.accept()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (room_code,))
    room = cursor.fetchone()
    if not room:
        await websocket.close()
        conn.close()
        return

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        await websocket.close()
        conn.close()
        return

    cursor.execute("SELECT * FROM stories WHERE id = ?", (room["story_id"],))
    story = cursor.fetchone()

    cursor.execute("""
        SELECT pm.*, u.username FROM party_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.room_id = ?
    """, (room["id"],))
    members = cursor.fetchall()
    conn.close()

    # 연결 등록
    if room_code not in room_connections:
        room_connections[room_code] = []
    room_connections[room_code].append((websocket, user_id, user["username"]))

    # 입장 알림
    await broadcast(room_code, {
        "type": "system",
        "message": f"{user['username']}님이 입장했습니다.",
        "members": [m["username"] for _, _, m in room_connections[room_code]]
    }, exclude=None)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            msg_type = payload.get("type", "chat")  # chat or start

            if msg_type == "start":
                # 스토리 시작 — AI 첫 나레이션
                members_info = "\n".join([
                    f"- {m['username']}: {m['character_stats']}"
                    for m in members
                ])

                prompt = f"""
{story['system_prompt']}

현재 참여자:
{members_info}

지금부터 파티 롤플레잉을 시작한다.
참여자들의 캐릭터 설정을 반영하여 스토리를 시작해줘.
나레이션과 NPC 대사를 포함하여 첫 장면을 묘사해줘.
"""
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": "스토리 시작"}]}],
                    config={"system_instruction": prompt, "max_output_tokens": 1000}
                )

                ai_response = response.text

                # DB 저장
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO party_messages (room_id, message_type, content)
                    VALUES (?, ?, ?)
                """, (room["id"], "narration", ai_response))
                cursor.execute("UPDATE party_rooms SET status = 'playing' WHERE id = ?",
                               (room["id"],))
                conn.commit()
                conn.close()

                await broadcast(room_code, {
                    "type": "narration",
                    "message": ai_response
                }, exclude=None)

            elif msg_type == "chat":
                # 유저 메시지 브로드캐스트
                await broadcast(room_code, {
                    "type": "chat",
                    "username": user["username"],
                    "message": message
                }, exclude=None)

                # DB 저장
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO party_messages (room_id, user_id, message_type, content)
                    VALUES (?, ?, ?, ?)
                """, (room["id"], user_id, "chat", message))
                conn.commit()

                # 최근 대화 기록 가져와서 AI 응답
                cursor.execute("""
                    SELECT * FROM party_messages
                    WHERE room_id = ?
                    ORDER BY created_at DESC LIMIT 20
                """, (room["id"],))
                recent = cursor.fetchall()
                conn.close()

                history_text = "\n".join([
                    f"[{m['message_type']}] {m['content']}"
                    for m in reversed(recent)
                ])

                members_info = "\n".join([
                    f"- {m['username']}: {m['character_stats']}"
                    for m in members
                ])

                prompt = f"""
{story['system_prompt']}

참여자 정보:
{members_info}

지금까지의 대화:
{history_text}

위 상황에서 나레이터로서 스토리를 자연스럽게 이어가줘.
필요하면 NPC 대사도 포함해줘.
"""
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": message}]}],
                    config={"system_instruction": prompt, "max_output_tokens": 1000}
                )

                ai_response = response.text

                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO party_messages (room_id, message_type, content)
                    VALUES (?, ?, ?)
                """, (room["id"], "narration", ai_response))
                conn.commit()
                conn.close()

                await broadcast(room_code, {
                    "type": "narration",
                    "message": ai_response
                }, exclude=None)

    except WebSocketDisconnect:
        room_connections[room_code] = [
            (ws, uid, uname)
            for ws, uid, uname in room_connections[room_code]
            if uid != user_id
        ]
        await broadcast(room_code, {
            "type": "system",
            "message": f"{user['username']}님이 퇴장했습니다."
        }, exclude=None)

        if not room_connections[room_code]:
            del room_connections[room_code]


async def broadcast(room_code: str, data: dict, exclude):
    if room_code not in room_connections:
        return
    for ws, uid, uname in room_connections[room_code]:
        if exclude and uid == exclude:
            continue
        try:
            await ws.send_text(json.dumps(data, ensure_ascii=False))
        except:
            pass