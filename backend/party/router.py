from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from deps import get_current_user
from google import genai
from dotenv import load_dotenv
import os
import json
import random
import string

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

router = APIRouter(prefix="/party", tags=["파티챗"])

room_connections: dict[str, list[tuple]] = {}
kick_votes: dict[str, dict[int, dict[int, str]]] = {}

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class CreateRoomRequest(BaseModel):
    story_id: int
    max_members: int = 4

class JoinRoomRequest(BaseModel):
    code: str
    character_stats: dict
    
class RoomSettingsRequest(BaseModel):
    output_multiplier: float = 1.0

class CreateStoryRequest(BaseModel):
    title: str
    genre: str = "기타"
    background: str
    system_prompt: str
    image_url: str = ""
    recommended_players: int = 4
    min_players: int = 2
    max_players: int = 6


def get_party_tokens(user_id: int, room_code: str) -> int:
    member_count = len(room_connections.get(room_code, []))
    member_count = max(member_count, 1)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT output_multiplier FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    conn.close()
    multiplier = u["output_multiplier"] if u and u["output_multiplier"] else 1.0
    return min(int(1000 * member_count * multiplier), 8000)


@router.get("/stories", summary="스토리 목록")
async def get_stories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories ORDER BY is_official DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("/stories", summary="스토리 생성")
async def create_story(
        request: CreateStoryRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stories (user_id, title, genre, background, system_prompt, image_url,
                            recommended_players, min_players, max_players)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        current_user["id"], request.title, request.genre,
        request.background, request.system_prompt, request.image_url,
        request.recommended_players, request.min_players, request.max_players
    ))
    conn.commit()
    story_id = cursor.lastrowid
    conn.close()
    return {"id": story_id, "message": "스토리 생성 완료"}


@router.post("/rooms", summary="파티방 생성")
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


@router.post("/rooms/join", summary="파티방 참여")
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


@router.get("/rooms/{code}", summary="파티방 정보")
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

    if room_code not in room_connections:
        room_connections[room_code] = []
    room_connections[room_code].append((websocket, user_id, user["username"]))

    await broadcast(room_code, {
        "type": "system",
        "message": f"{user['username']}님이 입장했습니다.",
        "members": [m for _, _, m in room_connections[room_code]]
    }, exclude=None)

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            message = payload.get("message", "")
            msg_type = payload.get("type", "chat")

            if msg_type == "start":
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
                party_tokens = get_party_tokens(user_id, room_code)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": "스토리 시작"}]}],
                    config={"system_instruction": prompt, "max_output_tokens": party_tokens}
                )
                ai_response = response.text

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
                await broadcast(room_code, {
                    "type": "chat",
                    "username": user["username"],
                    "message": message
                }, exclude=None)

                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO party_messages (room_id, user_id, message_type, content)
                    VALUES (?, ?, ?, ?)
                """, (room["id"], user_id, "chat", message))
                conn.commit()

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
                party_tokens = get_party_tokens(user_id, room_code)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": message}]}],
                    config={"system_instruction": prompt, "max_output_tokens": party_tokens}
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

            elif msg_type == "kick_vote":
                target_id = payload.get("target_user_id")
                member_count = len(room_connections.get(room_code, []))

                if member_count <= 2:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "2인 파티에서는 강퇴 투표를 사용할 수 없습니다."
                    }, ensure_ascii=False))
                    continue

                if target_id == user_id:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "본인을 강퇴할 수 없습니다."
                    }, ensure_ascii=False))
                    continue

                if room_code not in kick_votes:
                    kick_votes[room_code] = {}
                kick_votes[room_code][target_id] = {user_id: "yes"}

                target_name = next(
                    (uname for _, uid, uname in room_connections.get(room_code, [])
                     if uid == target_id), "알 수 없음"
                )

                await broadcast(room_code, {
                    "type": "kick_vote_started",
                    "target_user_id": target_id,
                    "target_username": target_name,
                    "proposer_id": user_id,
                    "proposer_username": user["username"],
                    "message": f"{user['username']}님이 {target_name}님 강퇴를 제안했습니다. 찬반 투표를 해주세요."
                }, exclude=None)

            elif msg_type == "kick_vote_result":
                target_id = payload.get("target_user_id")
                vote = payload.get("vote")

                if room_code not in kick_votes or target_id not in kick_votes[room_code]:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "진행 중인 투표가 없습니다."
                    }, ensure_ascii=False))
                    continue

                kick_votes[room_code][target_id][user_id] = vote

                member_count = len(room_connections.get(room_code, []))
                votes = kick_votes[room_code][target_id]
                yes_count = sum(1 for v in votes.values() if v == "yes")
                no_count = sum(1 for v in votes.values() if v == "no")

                await broadcast(room_code, {
                    "type": "kick_vote_update",
                    "target_user_id": target_id,
                    "yes": yes_count,
                    "no": no_count,
                    "total_members": member_count
                }, exclude=None)

                if yes_count > member_count // 2:
                    target_ws = next(
                        (ws for ws, uid, _ in room_connections.get(room_code, [])
                         if uid == target_id), None
                    )
                    target_name = next(
                        (uname for _, uid, uname in room_connections.get(room_code, [])
                         if uid == target_id), "알 수 없음"
                    )

                    del kick_votes[room_code][target_id]

                    room_connections[room_code] = [
                        (ws, uid, uname)
                        for ws, uid, uname in room_connections[room_code]
                        if uid != target_id
                    ]

                    await broadcast(room_code, {
                        "type": "kick_result",
                        "target_user_id": target_id,
                        "target_username": target_name,
                        "message": f"{target_name}님이 강퇴되었습니다."
                    }, exclude=None)

                    if target_ws:
                        try:
                            await target_ws.send_text(json.dumps({
                                "type": "kicked",
                                "message": "투표로 강퇴되었습니다."
                            }, ensure_ascii=False))
                            await target_ws.close()
                        except:
                            pass

                elif no_count >= member_count // 2 + 1:
                    del kick_votes[room_code][target_id]
                    await broadcast(room_code, {
                        "type": "kick_vote_failed",
                        "target_user_id": target_id,
                        "message": "강퇴 투표가 부결되었습니다."
                    }, exclude=None)

    except WebSocketDisconnect:
        room_connections[room_code] = [
            (ws, uid, uname)
            for ws, uid, uname in room_connections[room_code]
            if uid != user_id
        ]

        if room_code in kick_votes:
            kick_votes[room_code].pop(user_id, None)
            for target_id in list(kick_votes[room_code].keys()):
                kick_votes[room_code][target_id].pop(user_id, None)

        await broadcast(room_code, {
            "type": "system",
            "message": f"{user['username']}님이 퇴장했습니다."
        }, exclude=None)

        if not room_connections[room_code]:
            del room_connections[room_code]
            if room_code in kick_votes:
                del kick_votes[room_code]


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


@router.post("/rooms/{code}/invite/{user_id}", summary="파티 초대")
async def invite_to_party(
        code: str,
        user_id: int,
        current_user: dict = Depends(get_current_user)):

    conn = get_db()
    cursor = conn.cursor()

    # 방 존재 확인
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")

    # 초대 대상 존재 확인
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    invitee = cursor.fetchone()
    if not invitee:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    # 본인 초대 불가
    if user_id == current_user["id"]:
        conn.close()
        raise HTTPException(status_code=400, detail="본인을 초대할 수 없습니다.")

    # 방 꽉 찼는지 확인
    cursor.execute("SELECT COUNT(*) as cnt FROM party_members WHERE room_id = ?", (room["id"],))
    count = cursor.fetchone()["cnt"]
    if count >= room["max_members"]:
        conn.close()
        raise HTTPException(status_code=400, detail="방이 꽉 찼습니다.")

    try:
        cursor.execute("""
            INSERT INTO party_invitations (room_code, inviter_id, invitee_id)
            VALUES (?, ?, ?)
        """, (code, current_user["id"], user_id))
        conn.commit()
        conn.close()
        return {
            "message": f"{invitee['username']}님을 초대했습니다.",
            "room_code": code
        }
    except:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 초대한 사용자입니다.")


@router.get("/invitations/me", summary="내 파티 초대 목록")
async def get_my_party_invitations(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pi.*, u.username as inviter_name,
               pr.story_id, pr.max_members, pr.status as room_status
        FROM party_invitations pi
        JOIN users u ON pi.inviter_id = u.id
        JOIN party_rooms pr ON pi.room_code = pr.code
        WHERE pi.invitee_id = ? AND pi.status = 'pending'
        ORDER BY pi.created_at DESC
    """, (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.patch("/invitations/{invitation_id}/accept", summary="파티 초대 수락")
async def accept_party_invitation(
        invitation_id: int,
        current_user: dict = Depends(get_current_user)):

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_invitations WHERE id = ? AND invitee_id = ?",
                   (invitation_id, current_user["id"]))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="초대를 찾을 수 없습니다.")

    cursor.execute("UPDATE party_invitations SET status = 'accepted' WHERE id = ?",
                   (invitation_id,))
    conn.commit()
    conn.close()

    return {"message": "초대 수락 완료", "room_code": inv["room_code"]}


@router.patch("/invitations/{invitation_id}/reject", summary="파티 초대 거절")
async def reject_party_invitation(
        invitation_id: int,
        current_user: dict = Depends(get_current_user)):

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_invitations WHERE id = ? AND invitee_id = ?",
                   (invitation_id, current_user["id"]))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="초대를 찾을 수 없습니다.")

    cursor.execute("UPDATE party_invitations SET status = 'rejected' WHERE id = ?",
                   (invitation_id,))
    conn.commit()
    conn.close()
    return {"message": "초대 거절 완료"}

@router.patch("/rooms/{code}/settings", summary="방 설정 변경 (방장 전용)")
async def update_room_settings(
        code: str,
        request: RoomSettingsRequest,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")
    if room["host_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="방장만 설정을 변경할 수 있습니다.")

    # 방 전체 출력 배율 broadcast
    if code in room_connections:
        import json
        for ws, _, _ in room_connections[code]:
            try:
                await ws.send_text(json.dumps({
                    "type": "settings_updated",
                    "output_multiplier": request.output_multiplier,
                }, ensure_ascii=False))
            except:
                pass

    conn.close()
    return {"message": "설정 변경 완료"}


@router.delete("/rooms/{code}/leave", summary="방 나가기")
async def leave_room(
        code: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")

    cursor.execute("DELETE FROM party_members WHERE room_id = ? AND user_id = ?",
                   (room["id"], current_user["id"]))

    # 방장이 나가면 방 삭제
    if room["host_id"] == current_user["id"]:
        cursor.execute("DELETE FROM party_members WHERE room_id = ?", (room["id"],))
        cursor.execute("DELETE FROM party_rooms WHERE id = ?", (room["id"],))

    conn.commit()
    conn.close()
    return {"message": "방 나가기 완료"}

@router.patch("/rooms/{code}/delegate/{user_id}", summary="방장 위임")
async def delegate_host(
        code: str,
        user_id: int,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")
    if room["host_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="방장만 위임할 수 있습니다.")

    cursor.execute("SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
                   (room["id"], user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="해당 멤버를 찾을 수 없습니다.")

    cursor.execute("UPDATE party_rooms SET host_id = ? WHERE code = ?", (user_id, code))
    conn.commit()

    # WebSocket 브로드캐스트
    new_host_name = next(
        (uname for _, uid, uname in room_connections.get(code, []) if uid == user_id),
        "알 수 없음"
    )
    import json
    if code in room_connections:
        for ws, _, _ in room_connections[code]:
            try:
                await ws.send_text(json.dumps({
                    "type": "host_delegated",
                    "new_host_id": user_id,
                    "new_host_username": new_host_name,
                    "message": f"{new_host_name}님이 새 방장이 됐습니다.",
                }, ensure_ascii=False))
            except:
                pass

    conn.close()
    return {"message": f"방장을 {new_host_name}님에게 위임했습니다."}


# 파티 로그 조회
@router.get("/rooms/{code}/log", summary="파티 로그 조회")
async def get_party_log(
        code: str,
        current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")

    cursor.execute("""
        SELECT pm.*, u.username FROM party_messages pm
        LEFT JOIN users u ON pm.user_id = u.id
        WHERE pm.room_id = ?
        ORDER BY pm.created_at ASC
    """, (room["id"],))
    messages = cursor.fetchall()
    conn.close()
    return [dict(m) for m in messages]


# 파티 로그 PDF 내보내기
@router.get("/rooms/{code}/log/export", summary="파티 로그 PDF 내보내기")
async def export_party_log(
        code: str,
        current_user: dict = Depends(get_current_user)):
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")

    cursor.execute("""
        SELECT pm.*, u.username FROM party_messages pm
        LEFT JOIN users u ON pm.user_id = u.id
        WHERE pm.room_id = ?
        ORDER BY pm.created_at ASC
    """, (room["id"],))
    messages = cursor.fetchall()

    cursor.execute("SELECT title FROM stories WHERE id = ?", (room["story_id"],))
    story = cursor.fetchone()
    conn.close()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_name = "Helvetica"
    font_path = "NanumGothic-Regular.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
        font_name = "NanumGothic"

    c.setFont(font_name, 16)
    c.drawString(50, height - 50, f"파티챗 로그 - {story['title'] if story else code}")
    c.setFont(font_name, 9)
    c.drawString(50, height - 70, f"방 코드: {code} | 총 {len(messages)}개 메시지")

    y = height - 100
    line_height = 16
    margin = 50
    max_width = width - margin * 2

    for msg in messages:
        if y < 80:
            c.showPage()
            y = height - 50

        msg_type = msg["message_type"]
        username = msg["username"] or "나레이터"
        content = msg["content"]
        created_at = msg["created_at"]

        if msg_type == "narration":
            c.setFillColorRGB(0.5, 0.3, 0.9)
            label = f"[나레이션] {created_at[:16]}"
        else:
            c.setFillColorRGB(0.1, 0.5, 0.8)
            label = f"[{username}] {created_at[:16]}"

        c.setFont(font_name, 10)
        c.drawString(margin, y, label)
        y -= line_height

        c.setFillColorRGB(0, 0, 0)
        c.setFont(font_name, 9)
        line = ""
        for char in content:
            test = line + char
            if c.stringWidth(test, font_name, 9) > max_width:
                if y < 60:
                    c.showPage()
                    y = height - 50
                c.drawString(margin + 10, y, line)
                y -= line_height
                line = char
            else:
                line = test
        if line:
            if y < 60:
                c.showPage()
                y = height - 50
            c.drawString(margin + 10, y, line)
            y -= line_height

        y -= 8

    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=party_log_{code}.pdf"}
    )