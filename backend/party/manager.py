"""파티챗 연결 관리.

기존 WebSocket 핸들러는 받은 메시지를 **보낸 사람에게만** 되돌려 줬다.
브로드캐스트도, party_messages 저장도, AI 진행도 없어서 화면만 있고 기능은 없는 상태였다.
"""
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger("party")


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def join(self, room_code: str, websocket) -> None:
        async with self._lock:
            self._rooms[room_code].add(websocket)

    async def leave(self, room_code: str, websocket) -> None:
        async with self._lock:
            self._rooms[room_code].discard(websocket)
            if not self._rooms[room_code]:
                self._rooms.pop(room_code, None)

    async def broadcast(self, room_code: str, payload: dict, exclude=None) -> None:
        async with self._lock:
            targets = list(self._rooms.get(room_code, ()))
        dead = []
        for ws in targets:
            if ws is exclude:
                continue
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            await self.leave(room_code, ws)

    def count(self, room_code: str) -> int:
        return len(self._rooms.get(room_code, ()))


manager = RoomManager()
