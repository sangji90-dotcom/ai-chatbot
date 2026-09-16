"""파티챗 회귀 테스트.

FE 화면은 있는데 서버 라우터가 없어 404 나던 것들과,
WebSocket 이 타입 어노테이션 누락으로 연결조차 안 되던 문제를 고정한다.
"""
import pytest

from tests.conftest import auth


class _R:
    def __init__(self, t):
        self._t = t
        self.candidates = None

    @property
    def text(self):
        return self._t


@pytest.fixture
def fake_narrator(monkeypatch):
    n = {"i": 0}

    async def gen(contents, system_instruction, max_output_tokens,
                  apply_safety=True, timeout=60.0):
        if "기억해야 할" in system_instruction:
            return _R("없음")
        n["i"] += 1
        return _R(f"[나레이션 #{n['i']}] 숲길이 펼쳐진다.")

    from chat import llm
    import party.narrator as nar
    monkeypatch.setattr(llm, "generate", gen)
    monkeypatch.setattr(nar.llm, "generate", gen)
    return n


def _story(client, tok, title="테스트 스토리"):
    r = client.post("/party/stories", headers=auth(tok), json={
        "title": title, "genre": "판타지", "background": "안개 낀 숲",
        "system_prompt": "너는 진행자다.",
        "min_players": 2, "max_players": 6, "recommended_players": 4,
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _room(client, tok, story_id=None):
    r = client.post("/party/rooms", headers=auth(tok),
                    json={"story_id": story_id, "max_members": 4})
    assert r.status_code == 200, r.text
    return r.json()["code"]


def _uid(client, tok):
    return client.get("/users/me", headers=auth(tok)).json()["id"]


# ── 스토리 (기존엔 생성 경로가 아예 없었다) ─────────────────────────────
def test_story_create_and_list(client, user_a):
    sid = _story(client, user_a, "스토리생성")
    stories = client.get("/party/stories", headers=auth(user_a)).json()
    assert any(s["id"] == sid for s in stories)


def test_story_player_range_validated(client, user_a):
    r = client.post("/party/stories", headers=auth(user_a), json={
        "title": "잘못된범위", "genre": "판타지", "background": "x",
        "system_prompt": "y", "min_players": 6, "max_players": 3,
        "recommended_players": 4})
    assert r.status_code in (400, 422)


def test_story_delete_requires_owner(client, user_a, user_b):
    sid = _story(client, user_a, "삭제권한")
    assert client.delete(f"/party/stories/{sid}", headers=auth(user_b)).status_code == 403
    assert client.delete(f"/party/stories/{sid}", headers=auth(user_a)).status_code == 200


# ── 초대 (테이블만 있고 라우터가 없었다) ────────────────────────────────
def test_invitation_flow(client, user_a, user_b):
    code = _room(client, user_a)
    bid = _uid(client, user_b)

    sent = client.post("/party/invitations", headers=auth(user_a),
                       json={"code": code, "invitee_id": bid})
    assert sent.status_code == 200, sent.text

    inbox = client.get("/party/invitations/me", headers=auth(user_b)).json()
    assert len(inbox) == 1
    assert inbox[0]["room_code"] == code
    assert "inviter_name" in inbox[0], "FE 가 inviter_name 을 표시한다"

    acc = client.patch(f"/party/invitations/{inbox[0]['id']}/accept", headers=auth(user_b))
    assert acc.status_code == 200
    members = client.get(f"/party/rooms/{code}", headers=auth(user_a)).json()["members"]
    assert len(members) == 2


def test_invitation_reject_removes_from_inbox(client, user_a, user_b):
    code = _room(client, user_a)
    bid = _uid(client, user_b)
    client.post("/party/invitations", headers=auth(user_a),
                json={"code": code, "invitee_id": bid})
    inv = client.get("/party/invitations/me", headers=auth(user_b)).json()[0]

    assert client.patch(f"/party/invitations/{inv['id']}/reject",
                        headers=auth(user_b)).status_code == 200
    assert client.get("/party/invitations/me", headers=auth(user_b)).json() == []


def test_invite_requires_membership(client, user_a, user_b):
    code = _room(client, user_a)
    # B 는 방 참가자가 아니므로 초대할 수 없다
    r = client.post("/party/invitations", headers=auth(user_b),
                    json={"code": code, "invitee_id": _uid(client, user_a)})
    assert r.status_code == 403


# ── 방 설정 / 위임 ──────────────────────────────────────────────────────
def test_settings_and_delegate_are_host_only(client, user_a, user_b):
    code = _room(client, user_a)
    client.post("/party/rooms/join", headers=auth(user_b),
                json={"code": code, "character_stats": {}})
    bid = _uid(client, user_b)

    assert client.patch(f"/party/rooms/{code}/settings", headers=auth(user_b),
                        json={"output_multiplier": 2.0}).status_code == 403
    assert client.patch(f"/party/rooms/{code}/settings", headers=auth(user_a),
                        json={"output_multiplier": 1.5}).status_code == 200

    assert client.patch(f"/party/rooms/{code}/delegate/{bid}",
                        headers=auth(user_b)).status_code == 403
    assert client.patch(f"/party/rooms/{code}/delegate/{bid}",
                        headers=auth(user_a)).status_code == 200

    room = client.get(f"/party/rooms/{code}", headers=auth(user_b)).json()["room"]
    assert room["host_id"] == bid


def test_settings_rejects_out_of_range(client, user_a):
    code = _room(client, user_a)
    assert client.patch(f"/party/rooms/{code}/settings", headers=auth(user_a),
                        json={"output_multiplier": 9.0}).status_code == 400


# ── WebSocket (타입 어노테이션 누락으로 연결 자체가 안 됐다) ────────────
def test_websocket_connects_and_narrates(client, user_a, fake_narrator):
    sid = _story(client, user_a, "WS스토리")
    code = _room(client, user_a, sid)
    uid = _uid(client, user_a)

    with client.websocket_connect(f"/party/ws/{code}/{uid}") as ws:
        ws.send_json({"type": "auth", "token": user_a["access_token"]})
        assert ws.receive_json()["type"] == "auth_success", (
            "websocket 파라미터에 타입 어노테이션이 없으면 쿼리 파라미터로 해석돼 즉시 끊긴다"
        )
        ws.receive_json()  # 입장 안내

        ws.send_json({"type": "start"})
        seen = []
        for _ in range(4):
            m = ws.receive_json()
            seen.append(m["type"])
            if m["type"] == "narration":
                assert "나레이션" in m["message"]
                break
        assert "narration" in seen, f"start 후 AI 가 장면을 열어야 한다: {seen}"


def test_websocket_rejects_bad_token(client, user_a):
    code = _room(client, user_a)
    uid = _uid(client, user_a)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/party/ws/{code}/{uid}") as ws:
            ws.send_json({"type": "auth", "token": "invalid"})
            ws.receive_json()


def test_websocket_auto_narrates_after_turns(client, user_a, fake_narrator):
    import party.narrator as nar
    sid = _story(client, user_a, "자동진행")
    code = _room(client, user_a, sid)
    uid = _uid(client, user_a)

    with client.websocket_connect(f"/party/ws/{code}/{uid}") as ws:
        ws.send_json({"type": "auth", "token": user_a["access_token"]})
        ws.receive_json(); ws.receive_json()

        for i in range(nar.TURNS_BEFORE_NARRATION):
            ws.send_json({"type": "chat", "message": f"행동{i}"})

        seen = []
        for _ in range(12):
            m = ws.receive_json()
            seen.append(m["type"])
            if m["type"] == "narration":
                break
        assert "narration" in seen, f"발화가 쌓이면 AI 가 진행해야 한다: {seen}"


def test_party_messages_are_persisted(client, user_a, fake_narrator):
    code = _room(client, user_a)
    uid = _uid(client, user_a)
    with client.websocket_connect(f"/party/ws/{code}/{uid}") as ws:
        ws.send_json({"type": "auth", "token": user_a["access_token"]})
        ws.receive_json(); ws.receive_json()
        ws.send_json({"type": "chat", "message": "기록되나"})
        ws.receive_json()

    msgs = client.get(f"/party/rooms/{code}/messages", headers=auth(user_a)).json()
    assert any(m["content"] == "기록되나" for m in msgs)


def test_room_create_cooldown_blocks_spam(client, user_a, monkeypatch):
    """도배 방지 쿨다운. 테스트 전반은 0 으로 두고 여기서만 실제 값으로 확인한다."""
    import party.router as pr

    # 쿨다운이 0 인 상태에서 기준 방을 하나 만든 뒤,
    # 그 다음 요청부터 실제 쿨다운을 적용해 차단되는지 본다.
    first = client.post("/party/rooms", headers=auth(user_a), json={"max_members": 4})
    assert first.status_code == 200, first.text

    monkeypatch.setattr(pr, "ROOM_CREATE_COOLDOWN_SEC", 600)
    second = client.post("/party/rooms", headers=auth(user_a), json={"max_members": 4})
    assert second.status_code == 429
