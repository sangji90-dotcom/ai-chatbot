from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db
from core.db import read_only, transaction
from deps import get_current_user
from core.security import decode_token
from party.manager import manager
from party import narrator
from datetime import datetime, timedelta
import random
import string
import json
import logging
import asyncio
import sqlite3

from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/party", tags=["party"])
logger = logging.getLogger("party")

from core.config import PARTY_ROOM_COOLDOWN_SEC as ROOM_CREATE_COOLDOWN_SEC


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
async def party_websocket(websocket: WebSocket, room_code: str, user_id: int):
    """인증 -> 멤버십 확인 -> 브로드캐스트 루프.

    주의: websocket 파라미터에 타입 어노테이션이 없으면 FastAPI 가 이를
    쿼리 파라미터로 해석해 연결이 즉시 끊긴다. 실제로 그 상태였고,
    그래서 파티챗은 연결 자체가 된 적이 없었다.

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

                started = False
                with transaction() as cur:
                    cur.execute(
                        "UPDATE party_rooms SET status = 'active' "
                        " WHERE id = ? AND status = 'waiting'",
                        (room_id,),
                    )
                    started = cur.rowcount > 0
                if not started:
                    await websocket.send_json(
                        {"type": "error", "message": "이미 시작된 방이에요."}
                    )
                    continue

                await manager.broadcast(room_code, {"type": "system", "message": "✦ 이야기가 시작됩니다..."})
                await _narrate(room_code, room_id, opener=True)

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

                # 플레이어 발화가 일정 수 쌓이면 AI 가 이야기를 진행한다.
                # 매 발화마다 돌리면 비용과 대기가 커지고, 너무 늦으면 대화가 붕 뜬다.
                with read_only() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) AS cnt FROM party_messages
                         WHERE room_id = ? AND message_type = 'chat'
                           AND id > COALESCE(
                               (SELECT MAX(id) FROM party_messages
                                 WHERE room_id = ? AND message_type = 'narration'), 0)
                        """,
                        (room_id, room_id),
                    )
                    pending = cur.fetchone()["cnt"]

                if pending >= narrator.TURNS_BEFORE_NARRATION:
                    await _narrate(room_code, room_id)

            elif msg_type == "narrate":
                # 플레이어가 직접 진행을 요청 (턴이 안 찼을 때)
                await _narrate(room_code, room_id)

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


async def _narrate(room_code: str, room_id: int, opener: bool = False) -> None:
    """AI 진행 1회. 실패해도 방이 죽지 않도록 안내만 내보낸다."""
    await manager.broadcast(room_code, {"type": "narrating"})
    try:
        with read_only() as cur:
            cur.execute("SELECT * FROM party_rooms WHERE id = ?", (room_id,))
            room = dict(cur.fetchone())

        text = await (narrator.open_scene(room) if opener else narrator.advance(room))
        if not text:
            raise ValueError("빈 응답")

        with transaction() as cur:
            cur.execute(
                "INSERT INTO party_messages (room_id, user_id, message_type, content) "
                "VALUES (?, NULL, 'narration', ?)",
                (room_id, text),
            )
            message_id = cur.lastrowid

        await manager.broadcast(room_code, {
            "type": "narration", "message_id": message_id, "message": text,
        })
    except Exception:  # noqa: BLE001
        logger.exception("narration failed room=%s", room_code)
        await manager.broadcast(room_code, {
            "type": "system",
            "message": "진행자가 잠시 말을 잃었어요. 대화를 이어가면 다시 이어집니다.",
        })


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


# ══════════════════════════════════════════════════════════════════════
# 아래는 FE 화면이 이미 존재하는데 서버 라우터가 없어 404 나던 것들이다.
# (party_invitations 테이블도 만들어만 두고 한 번도 쓰이지 않았다)
# ══════════════════════════════════════════════════════════════════════

class InviteRequest(BaseModel):
    code: str
    invitee_id: int


class RoomSettingsRequest(BaseModel):
    output_multiplier: Optional[float] = None
    max_members: Optional[int] = None


@router.post("/invitations", summary="파티 초대 보내기")
def send_invitation(request: InviteRequest,
                    current_user: dict = Depends(get_current_user)):
    code = request.code.upper()
    if request.invitee_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="본인은 초대할 수 없어요.")

    with transaction() as cur:
        cur.execute("SELECT * FROM party_rooms WHERE code = ?", (code,))
        room = cur.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
        if room["status"] == "closed":
            raise HTTPException(status_code=410, detail="방이 종료됐어요")

        # 방 참가자만 초대할 수 있다
        cur.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], current_user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=403, detail="참가한 방이 아니에요")

        cur.execute("SELECT id FROM users WHERE id = ?", (request.invitee_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 차단 관계면 초대할 수 없다
        cur.execute(
            "SELECT 1 FROM user_blocks WHERE (blocker_id = ? AND blocked_id = ?) "
            "   OR (blocker_id = ? AND blocked_id = ?)",
            (request.invitee_id, current_user["id"], current_user["id"], request.invitee_id),
        )
        if cur.fetchone():
            raise HTTPException(status_code=403, detail="초대할 수 없는 상대예요.")

        try:
            cur.execute(
                "INSERT INTO party_invitations (room_code, inviter_id, invitee_id) "
                "VALUES (?, ?, ?)",
                (code, current_user["id"], request.invitee_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="이미 초대한 상대예요.")

    from notifications.router import send_notification
    send_notification(
        request.invitee_id, "party_invite", "파티 초대가 도착했어요",
        f"{current_user['username']}님이 파티에 초대했어요 (코드 {code})",
        "/party",
    )
    return {"message": "초대를 보냈어요"}


@router.get("/invitations/me", summary="내가 받은 초대")
def my_invitations(current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        cur.execute(
            """
            SELECT pi.id, pi.room_code, pi.created_at,
                   u.username AS inviter_name
              FROM party_invitations pi
              JOIN users u ON pi.inviter_id = u.id
              JOIN party_rooms pr ON pr.code = pi.room_code
             WHERE pi.invitee_id = ?
               AND pi.status = 'pending'
               AND pr.status != 'closed'
             ORDER BY pi.created_at DESC
            """,
            (current_user["id"],),
        )
        return [dict(r) for r in cur.fetchall()]


@router.patch("/invitations/{invitation_id}/accept", summary="초대 수락")
def accept_invitation(invitation_id: int,
                      current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute(
            "SELECT * FROM party_invitations WHERE id = ? AND invitee_id = ?",
            (invitation_id, current_user["id"]),
        )
        inv = cur.fetchone()
        if not inv or inv["status"] != "pending":
            raise HTTPException(status_code=404, detail="초대를 찾을 수 없습니다")

        cur.execute("SELECT * FROM party_rooms WHERE code = ?", (inv["room_code"],))
        room = cur.fetchone()
        if not room or room["status"] == "closed":
            cur.execute(
                "UPDATE party_invitations SET status = 'expired' WHERE id = ?", (invitation_id,)
            )
            raise HTTPException(status_code=410, detail="방이 종료됐어요")

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM party_members WHERE room_id = ?", (room["id"],)
        )
        if cur.fetchone()["cnt"] >= room["max_members"]:
            raise HTTPException(status_code=400, detail="방이 가득 찼어요")

        cur.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], current_user["id"]),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO party_members (room_id, user_id, character_stats) VALUES (?, ?, ?)",
                (room["id"], current_user["id"], json.dumps({})),
            )
        cur.execute(
            "UPDATE party_invitations SET status = 'accepted' WHERE id = ?", (invitation_id,)
        )
        code = room["code"]

    return {"message": "초대를 수락했어요", "code": code}


@router.patch("/invitations/{invitation_id}/reject", summary="초대 거절")
def reject_invitation(invitation_id: int,
                      current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute(
            "UPDATE party_invitations SET status = 'rejected' "
            " WHERE id = ? AND invitee_id = ? AND status = 'pending'",
            (invitation_id, current_user["id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="초대를 찾을 수 없습니다")
    return {"message": "초대를 거절했어요"}


@router.patch("/rooms/{code}/settings", summary="방 설정 변경 (방장)")
def update_room_settings(code: str, request: RoomSettingsRequest,
                         current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute("SELECT * FROM party_rooms WHERE code = ?", (code.upper(),))
        room = cur.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
        if room["host_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="방장만 변경할 수 있어요")

        fields, params = [], []
        if request.output_multiplier is not None:
            if not (0.5 <= request.output_multiplier <= 3.0):
                raise HTTPException(status_code=400, detail="응답 길이 배율은 0.5~3.0 이어야 해요")
            fields.append("output_multiplier = ?")
            params.append(request.output_multiplier)
        if request.max_members is not None:
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM party_members WHERE room_id = ?", (room["id"],)
            )
            current = cur.fetchone()["cnt"]
            if not (2 <= request.max_members <= 10):
                raise HTTPException(status_code=400, detail="정원은 2~10명이어야 해요")
            if request.max_members < current:
                raise HTTPException(status_code=400, detail="현재 인원보다 적게 줄일 수 없어요")
            fields.append("max_members = ?")
            params.append(request.max_members)

        if fields:
            params.append(room["id"])
            cur.execute(f"UPDATE party_rooms SET {', '.join(fields)} WHERE id = ?", params)

    return {"message": "설정을 변경했어요"}


@router.patch("/rooms/{code}/delegate/{user_id}", summary="방장 위임")
def delegate_host(code: str, user_id: int,
                  current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute("SELECT * FROM party_rooms WHERE code = ?", (code.upper(),))
        room = cur.fetchone()
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다")
        if room["host_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="방장만 위임할 수 있어요")
        if user_id == current_user["id"]:
            raise HTTPException(status_code=400, detail="이미 방장이에요")

        cur.execute(
            "SELECT id FROM party_members WHERE room_id = ? AND user_id = ?",
            (room["id"], user_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="방에 없는 사용자예요")

        cur.execute("UPDATE party_rooms SET host_id = ? WHERE id = ?", (user_id, room["id"]))

    return {"message": "방장을 위임했어요"}


class StoryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    genre: str = "기타"
    background: str = Field(min_length=1, max_length=4000)
    system_prompt: str = Field(min_length=1, max_length=8000)
    image_url: str = Field(default="", max_length=500)
    recommended_players: int = Field(default=4, ge=2, le=10)
    min_players: int = Field(default=2, ge=2, le=10)
    max_players: int = Field(default=6, ge=2, le=10)


@router.post("/stories", summary="스토리 생성")
def create_story(request: StoryRequest, current_user: dict = Depends(get_current_user)):
    """스토리를 만드는 경로가 아예 없어서 파티챗의 스토리 기반 플레이가
    통째로 불가능했다 (관리자 패널이 이 엔드포인트를 호출하는데 서버에 없었음)."""
    if request.min_players > request.max_players:
        raise HTTPException(status_code=400, detail="최소 인원이 최대 인원보다 클 수 없어요")
    if not (request.min_players <= request.recommended_players <= request.max_players):
        raise HTTPException(status_code=400, detail="권장 인원이 범위를 벗어났어요")

    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO stories
                (user_id, title, genre, background, system_prompt, image_url,
                 recommended_players, min_players, max_players, is_official)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (current_user["id"], request.title, request.genre, request.background,
             request.system_prompt, request.image_url, request.recommended_players,
             request.min_players, request.max_players,
             1 if current_user.get("is_admin") else 0),
        )
        story_id = cur.lastrowid
    return {"id": story_id, "message": "스토리를 만들었어요"}


@router.delete("/stories/{story_id}", summary="스토리 삭제")
def delete_story(story_id: int, current_user: dict = Depends(get_current_user)):
    with transaction() as cur:
        cur.execute("SELECT user_id FROM stories WHERE id = ?", (story_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="스토리를 찾을 수 없습니다")
        if row["user_id"] != current_user["id"] and not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="삭제 권한이 없어요")
        cur.execute(
            "UPDATE party_rooms SET story_id = NULL WHERE story_id = ?", (story_id,)
        )
        cur.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    return {"message": "스토리를 삭제했어요"}
