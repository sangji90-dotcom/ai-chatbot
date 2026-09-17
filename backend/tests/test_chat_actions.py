"""재생성 / 스트리밍 회귀 테스트.

둘 다 '10턴 도달률' 을 지키기 위한 기능이라, 조용히 망가지면
기억 품질 검증 자체가 불가능해진다.
"""
import asyncio
import json
import sqlite3

import pytest
from fastapi import HTTPException

from core.config import DB_PATH
from tests.conftest import auth


class _Resp:
    def __init__(self, text):
        self._t = text
        self.candidates = None

    @property
    def text(self):
        return self._t


@pytest.fixture
def fake_llm(monkeypatch):
    """LLM 을 결정적으로 대체한다. state 로 실패를 주입할 수 있다."""
    state = {"n": 0, "fail_stream": False, "fail_gen": False}

    async def gen(contents, system_instruction, max_output_tokens,
                  apply_safety=True, timeout=60.0):
        if "기억해야 할 정보만" in system_instruction:
            return _Resp("없음")
        if state["fail_gen"]:
            raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했어요.")
        state["n"] += 1
        return _Resp(f"응답#{state['n']} [EMOTION:happy] [SITUATION:cafe]")

    async def stream(contents, system_instruction, max_output_tokens, apply_safety=True):
        if state["fail_stream"]:
            raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했어요.")
        for c in ["스트", "리밍 ", "테스트", " [EMO", "TION:sad] [SITUATION:night]"]:
            await asyncio.sleep(0)
            yield c

    import chat.router as cr
    from chat import llm
    for mod in (llm, cr.llm):
        monkeypatch.setattr(mod, "generate", gen, raising=False)
        monkeypatch.setattr(mod, "generate_stream", stream, raising=False)
    return state


def _character(client, tok, name="재생성테스트"):
    r = client.post("/characters", headers=auth(tok), json={
        "name": name, "age": 25, "job": "바리스타", "personality": "다정함",
        "likes": "커피", "dislikes": "소음", "speech_style": "부드러움",
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _balance(client, tok):
    return client.get("/tokens/me", headers=auth(tok)).json()["token_balance"]


def _read_sse(resp):
    deltas, done, error = [], None, None
    event = None
    for line in resp.iter_lines():
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = json.loads(line.split(":", 1)[1])
            if event == "delta":
                deltas.append(data["text"])
            elif event == "done":
                done = data
            elif event == "error":
                error = data
    return deltas, done, error


# ── 재생성 ──────────────────────────────────────────────────────────────
def test_regenerate_replaces_instead_of_appending(client, user_a, fake_llm):
    cid = _character(client, user_a, "교체확인")
    first = client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "안녕", "session_id": "regen-1"}).json()

    again = client.post("/chat/regenerate", headers=auth(user_a), json={
        "character_id": cid, "session_id": "regen-1"})
    assert again.status_code == 200, again.text
    body = again.json()

    assert body["message_id"] == first["message_id"], "재생성은 기존 응답을 교체해야 한다"
    assert body["message"] != first["message"]

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM chat_history WHERE session_id = 'regen-1' ORDER BY id"
    ).fetchall()
    conn.close()
    assert [r[0] for r in rows] == ["user", "assistant"], "응답이 중복 적재되면 안 된다"
    assert rows[1][1] == body["message"]


def test_regenerate_without_response_is_400(client, user_a, fake_llm):
    cid = _character(client, user_a, "빈세션")
    r = client.post("/chat/regenerate", headers=auth(user_a), json={
        "character_id": cid, "session_id": "nothing-here"})
    assert r.status_code == 400


def test_regenerate_refunds_on_failure(client, user_a, fake_llm):
    cid = _character(client, user_a, "환급확인")
    client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "안녕", "session_id": "regen-2"})

    before = _balance(client, user_a)
    fake_llm["fail_gen"] = True
    r = client.post("/chat/regenerate", headers=auth(user_a), json={
        "character_id": cid, "session_id": "regen-2"})
    assert r.status_code == 502
    assert _balance(client, user_a) == before, "생성 실패 시 토큰이 증발하면 안 된다"


def test_regenerate_is_logged_as_signal(client, user_a, fake_llm):
    cid = _character(client, user_a, "계측확인")
    client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "안녕", "session_id": "regen-3"})
    client.post("/chat/regenerate", headers=auth(user_a), json={
        "character_id": cid, "session_id": "regen-3"})

    conn = sqlite3.connect(DB_PATH)
    n = conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type = 'regenerated'"
    ).fetchone()[0]
    conn.close()
    assert n >= 1, "재생성은 불만 신호이므로 계측에 남아야 한다"


def test_regenerate_blocks_other_users_session(client, user_a, user_b, fake_llm):
    cid = _character(client, user_a, "남의세션")
    client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "안녕", "session_id": "regen-4"})
    # B 가 A 의 session_id 를 알아도 자기 기록이 없으므로 재생성 불가
    r = client.post("/chat/regenerate", headers=auth(user_b), json={
        "character_id": cid, "session_id": "regen-4"})
    assert r.status_code == 400


# ── 스트리밍 ────────────────────────────────────────────────────────────
def test_stream_emits_deltas_without_leaking_tags(client, user_a, fake_llm):
    cid = _character(client, user_a, "스트림확인")
    with client.stream("POST", "/chat/stream", headers=auth(user_a), json={
            "character_id": cid, "message": "안녕", "session_id": "st-1"}) as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
        deltas, done, error = _read_sse(resp)

    joined = "".join(deltas)
    assert error is None
    assert len(deltas) >= 2, "한 번에 다 오면 스트리밍이 아니다"
    assert "EMOTION" not in joined and "SITUATION" not in joined, "태그가 화면에 새면 안 된다"
    assert "스트리밍 테스트" in joined
    assert done["emotion"] == "sad" and done["situation"] == "night"
    assert isinstance(done["message_id"], int)


def test_stream_persists_message(client, user_a, fake_llm):
    cid = _character(client, user_a, "저장확인")
    with client.stream("POST", "/chat/stream", headers=auth(user_a), json={
            "character_id": cid, "message": "기록되나", "session_id": "st-2"}) as resp:
        _, done, _ = _read_sse(resp)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT role, content FROM chat_history WHERE session_id = 'st-2' ORDER BY id"
    ).fetchall()
    conn.close()
    assert [r[0] for r in rows] == ["user", "assistant"]
    assert "EMOTION" not in rows[1][1], "저장본에도 태그가 남으면 안 된다"


def test_stream_refunds_on_failure(client, user_a, fake_llm):
    cid = _character(client, user_a, "스트림환급")
    before = _balance(client, user_a)
    fake_llm["fail_stream"] = True

    with client.stream("POST", "/chat/stream", headers=auth(user_a), json={
            "character_id": cid, "message": "실패", "session_id": "st-3"}) as resp:
        deltas, done, error = _read_sse(resp)

    assert error is not None and done is None
    assert error["refunded"] > 0
    assert _balance(client, user_a) == before, "스트림 실패 시 토큰이 증발하면 안 된다"


def test_stream_requires_auth(client):
    r = client.post("/chat/stream", json={
        "character_id": "x", "message": "hi", "session_id": "s"})
    assert r.status_code == 401


def test_stream_blocks_private_character(client, user_a, user_b, fake_llm):
    r = client.post("/characters", headers=auth(user_a), json={
        "name": "스트림비공개", "age": 25, "job": "개발자", "personality": "조용",
        "likes": "커피", "dislikes": "소음", "speech_style": "담백", "visibility": "private"})
    cid = r.json()["id"]
    resp = client.post("/chat/stream", headers=auth(user_b), json={
        "character_id": cid, "message": "안녕", "session_id": "st-4"})
    assert resp.status_code == 403


def test_session_list_returns_dates_frontend_reads(client, user_a, fake_llm):
    """FE 는 started_at / last_at 을 읽는데 서버가 last_chat 만 줘서
    세션 목록 날짜가 'Invalid Date' 로 표시됐다."""
    cid = _character(client, user_a, "세션날짜")
    client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "첫 메시지", "session_id": "date-1"})

    sessions = client.get(f"/chat/sessions/{cid}", headers=auth(user_a)).json()
    assert sessions, "세션이 있어야 한다"
    s = sessions[0]
    for field in ("session_id", "started_at", "last_at", "message_count"):
        assert field in s, f"FE 가 읽는 {field} 가 응답에 없다"
    assert s["started_at"] and s["last_at"]


# ── 출력 길이별 차등 과금 ────────────────────────────────────────────────
@pytest.mark.parametrize("length,expected", [("short", 30), ("medium", 50), ("long", 80)])
def test_chat_cost_follows_output_length(client, user_a, fake_llm, length, expected):
    """세 옵션 모두 50코인이 빠지는데 설정 화면은 300/1,000/2,000 이라고
    표시하고 있었다(그건 LLM 출력 토큰 상한이었다)."""
    cid = _character(client, user_a, f"과금{length}")
    client.patch("/users/me/settings", headers=auth(user_a), json={"output_length": length})

    r = client.post("/chat", headers=auth(user_a), json={
        "character_id": cid, "message": "안녕", "session_id": f"cost-{length}"})
    assert r.status_code == 200, r.text
    assert r.json()["cost"] == expected, "클라이언트가 하드코딩하지 않도록 실제 차감액을 내려준다"

    # 잔액 차이로 재면 업적 보상 지급에 오염된다 — 차감 내역을 직접 본다
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT amount FROM token_history WHERE token_type = 'use' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row[0] == -expected, f"{length} 설정의 실제 차감액이 {expected} 이어야 한다"


def test_pricing_endpoint_matches_actual_cost(client):
    r = client.get("/tokens/pricing")
    assert r.status_code == 200
    body = r.json()
    costs = {c["value"]: c["cost"] for c in body["chat"]}
    assert costs == {"short": 30, "medium": 50, "long": 80}
    assert body["rewards"]["signup"] == 3000
    assert body["event_token_expire_days"] == 21
