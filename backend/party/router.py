from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from core.db import read_only, transaction
from deps import get_current_user
from core.security import decode_token
from party.manager import manager
from datetime import datetime, timedelta
import random
import string
import json
import logging
import asyncio

from fastapi import WebSocketDisconnect

router = APIRouter(prefix="/party", tags=["party"])
logger = logging.getLogger("party")

ROOM_CREATE_COOLDOWN_SEC = 10


def generate_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class CreateRoomRequest(BaseModel):
    story_id: Optional[int] = None
    character_id: Optional[str] = None
    max_members: int = 4


class JoinRoomRequest(BaseModel):
    code: str
    character_stats: Optional[dict] = {}


@router.get("/stories", summary="스토리 목록")
async def get_stories(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories ORDER BY is_official DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("/rooms", summary="방 만들기")
async def create_room(
    request: CreateRoomRequest, current_user: dict = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT created_at FROM party_rooms WHERE host_id = ? ORDER BY created_at DESC LIMIT 1",
        (current_user["id"],),
    )
    last = cursor.fetchone()
    if last:
        last_time = datetime.fromisoformat(last["created_at"])
        if datetime.utcnow() - last_time < timedelta(seconds=ROOM_CREATE_COOLDOWN_SEC):
            conn.close()
            raise HTTPException(status_code=429, detail="잠시 후 다시 시도해주세요")

    story = None
    if request.story_id:
        cursor.execute("SELECT * FROM stories WHERE id = ?", (request.story_id,))
        story = cursor.fetchone()
        if not story:
            conn.close()
            raise HTTPException(status_code=404, detail="스토리를 찾을 수 없습니다")

    code = generate_code()
    while True:
        cursor.execute("SELECT id FROM party_rooms WHERE code = ?", (code,))
        if not cursor.fetchone():
            break
        code = generate_code()

    cursor.execute(
        """
        INSERT INTO party_rooms (code, host_id, story_id, character_id, max_members, status)
        VALUES (?, ?, ?, ?, ?, 'waiting')
    """,
        (
            code,
            current_user["id"],
            request.story_id,
            request.character_id,
            request.max_members,
        ),
    )

    room_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO party_members (room_id, user_id, character_stats)
        VALUES (?, ?, ?)
    """,
        (room_id, current_user["id"], json.dumps({})),
    )

    conn.commit()
    conn.close()
    return {"code": code, "room_id": room_id}


@router.post("/rooms/join", summary="코드로 방 입장")
async def join_room(
    request: JoinRoomRequest, current_user: dict = Depends(get_current_user)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (request.code.upper(),))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")

    if room["status"] != "waiting":
        conn.close()
        raise HTTPException(status_code=400, detail="이미 시작된 방이에요")

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM party_members WHERE room_id = ?", (room["id"],)
    )
    count = cursor.fetchone()["cnt"]
    if count >= room["max_members"]:
        conn.close()
        raise HTTPException(status_code=400, detail="방이 가득 찼어요")

    cursor.execute(
        "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
        (room["id"], current_user["id"]),
    )
    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO party_members (room_id, user_id, character_stats)
            VALUES (?, ?, ?)
        """,
            (room["id"], current_user["id"], json.dumps(request.character_stats or {})),
        )
        conn.commit()

    conn.close()
    return {"code": room["code"], "room_id": room["id"]}


@router.get("/rooms/{code}", summary="방 정보 조회")
async def get_room(code: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code.upper(),))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")

    if room["status"] == "closed":
        conn.close()
        raise HTTPException(status_code=410, detail="방이 종료됐어요")

    cursor.execute(
        "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
        (room["id"], current_user["id"]),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="참가한 방이 아니에요")

    cursor.execute(
        """
        SELECT pm.user_id, u.username, pm.character_stats
        FROM party_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.room_id = ?
    """,
        (room["id"],),
    )
    members = [dict(m) for m in cursor.fetchall()]

    conn.close()
    return {"room": dict(room), "members": members}


@router.delete("/rooms/{code}/leave", summary="방 나가기")
async def leave_room(code: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM party_rooms WHERE code = ?", (code.upper(),))
        room = cursor.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")

        cursor.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], current_user["id"]),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="참가한 방이 아니에요")

        cursor.execute(
            "DELETE FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], current_user["id"]),
        )

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM party_members WHERE room_id = ?", (room["id"],)
        )
        count = cursor.fetchone()["cnt"]
        if count == 0:
            cursor.execute(
                "UPDATE party_rooms SET status = 'closed' WHERE id = ?", (room["id"],)
            )

        conn.commit()
        return {"message": "방을 나갔어요"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="처리 중 오류가 발생했어요")
    finally:
        conn.close()


@router.websocket("/ws/{room_code}/{user_id}")
async def party_websocket(websocket, room_code: str, user_id: int):
    """인증 -> 멤버십 확인 -> 브로드캐스트 루프.

    변경점: 받은 메시지를 방 전체에 전파하고 party_messages 에 남긴다.
    (이전에는 보낸 사람에게만 에코해서 파티챗이 실제로 동작하지 않았다)
    """
    room_code = room_code.upper()
    await websocket.accept()

    # ── 인증: accept 직후 첫 메시지로 토큰을 받는다 (WS 는 헤더를 못 붙이는 클라가 많음) ──
    try:
        auth_msg = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
    except (asyncio.TimeoutError, Exception):
        await websocket.close(code=4401)
        return

    if not isinstance(auth_msg, dict) or auth_msg.get("type") != "auth":
        await websocket.close(code=4401)
        return

    payload = decode_token(auth_msg.get("token"), expected_type="access")
    if not payload or int(payload["sub"]) != user_id:
        await websocket.close(code=4401)
        return

    with read_only() as cur:
        cur.execute("SELECT suspended FROM users WHERE id = ?", (user_id,))
        u = cur.fetchone()
        if not u or u["suspended"]:
            await websocket.close(code=4403)
            return

        cur.execute("SELECT * FROM party_rooms WHERE code = ?", (room_code,))
        room = cur.fetchone()
        if not room:
            await websocket.close(code=4404)
            return
        if room["status"] == "closed":
            await websocket.close(code=4410)
            return

        cur.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], user_id),
        )
        if not cur.fetchone():
            await websocket.close(code=4403)
            return

        cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        username = row["username"] if row else "유저"

    room_id = room["id"]
    await manager.join(room_code, websocket)
    await websocket.send_json({"type": "auth_success"})

    try:
        await websocket.send_json(
            {"type": "system", "message": f"파티챗에 입장했어요! 방 코드: {room_code}"}
        )
        await manager.broadcast(
            room_code,
            {"type": "system", "message": f"{username}님이 입장했어요."},
            exclude=websocket,
        )

        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "start":
                if room["host_id"] != user_id:
                    await websocket.send_json(
                        {"type": "error", "message": "방장만 시작할 수 있어요."}
                    )
                    continue
                with transaction() as cur:
                    cur.execute(
                        "UPDATE party_rooms SET status = 'active' WHERE id = ? AND status = 'waiting'",
                        (room_id,),
                    )
                await manager.broadcast(room_code, {
                    "type": "narration",
                    "message": "✦ 파티챗이 시작됐어요! AI가 이야기를 이끌어갑니다.",
                })

            elif msg_type == "chat":
                message = (data.get("message") or "").strip()
                if not message:
                    continue
                if len(message) > 2000:
                    await websocket.send_json(
                        {"type": "error", "message": "메시지가 너무 길어요."}
                    )
                    continue

                with transaction() as cur:
                    cur.execute(
                        "INSERT INTO party_messages (room_id, user_id, message_type, content) "
                        "VALUES (?, ?, 'chat', ?)",
                        (room_id, user_id, message),
                    )
                    message_id = cur.lastrowid

                await manager.broadcast(room_code, {
                    "type": "chat",
                    "message_id": message_id,
                    "user_id": user_id,
                    "username": username,
                    "message": message,
                })

    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.exception("party ws error room=%s user=%s", room_code, user_id)
    finally:
        await manager.leave(room_code, websocket)
        await manager.broadcast(
            room_code, {"type": "system", "message": f"{username}님이 나갔어요."}
        )
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass


@router.get("/rooms/{code}/messages", summary="파티 메시지 기록")
def get_party_messages(code: str, limit: int = 100,
                       current_user: dict = Depends(get_current_user)):
    limit = min(max(1, limit), 500)
    with read_only() as cur:
        cur.execute("SELECT id FROM party_rooms WHERE code = ?", (code.upper(),))
        room = cur.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
        cur.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], current_user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="참가한 방이 아니에요")
        cur.execute(
            """
            SELECT pm.id, pm.user_id, pm.message_type, pm.content, pm.created_at, u.username
              FROM party_messages pm
              LEFT JOIN users u ON pm.user_id = u.id
             WHERE pm.room_id = ?
             ORDER BY pm.id DESC LIMIT ?
            """,
            (room["id"], limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
    return list(reversed(rows))
