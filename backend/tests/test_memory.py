"""기억(memory_book) 추출·주입 회귀 테스트.

CBT 의 검증 대상이 기억 품질이므로, 이 동작이 조용히 꺼지거나 새는 것을 막는다.
"""
import sqlite3

from chat import memory
from core.config import DB_PATH, MEMORY_FREE_CHUNKS
from tests.conftest import auth


def _uid(client, tok):
    return client.get("/users/me", headers=auth(tok)).json()["id"]


def _seed_memories(uid: int, cid: str, n: int):
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT INTO memory_book (user_id, character_id, title, content) VALUES (?, ?, '자동추출', ?)",
        [(uid, cid, f"기억 {i}") for i in range(n)],
    )
    conn.commit()
    conn.close()


# ── 추출 파싱 ───────────────────────────────────────────────────────────
def test_parse_drops_duplicates_of_known():
    known = [{"content": "유저의 이름은 지훈이다"}]
    out = memory.parse_extracted("유저의 이름은 지훈이다.\n유저는 고양이를 키운다", known)
    assert out == ["유저는 고양이를 키운다"], "이미 아는 기억이 또 쌓이면 프롬프트만 커진다"


def test_parse_handles_none_and_bullets():
    assert memory.parse_extracted("없음", []) == []
    assert memory.parse_extracted("", []) == []
    assert memory.parse_extracted("- 유저는 야근이 잦다\n2) 유저는 커피를 좋아한다", []) == [
        "유저는 야근이 잦다", "유저는 커피를 좋아한다",
    ]


def test_parse_caps_item_count():
    text = "\n".join(f"사실 {i}" for i in range(10))
    assert len(memory.parse_extracted(text, [])) <= memory.MEMORY_MAX_PER_EXTRACT


def test_parse_drops_overlong_lines():
    assert memory.parse_extracted("가" * 200, []) == []


# ── 주입 상한 ───────────────────────────────────────────────────────────
def test_injection_is_capped(client, user_a):
    """상한이 없으면 대화가 길어질수록 프롬프트가 무한히 커진다."""
    uid = _uid(client, user_a)
    cid = "cap-test-char"
    _seed_memories(uid, cid, MEMORY_FREE_CHUNKS + 25)

    loaded = memory.load_memories(uid, cid, MEMORY_FREE_CHUNKS)
    assert len(loaded) == MEMORY_FREE_CHUNKS
    assert memory.total_count(uid, cid) == MEMORY_FREE_CHUNKS + 25, "원본은 지우지 않는다"


def test_injection_keeps_newest(client, user_a):
    """오래된 기억이 최신 기억을 밀어내면 안 된다."""
    uid = _uid(client, user_a)
    cid = "recency-test-char"
    _seed_memories(uid, cid, 30)

    loaded = memory.load_memories(uid, cid, 5)
    assert [m["content"] for m in loaded] == ["기억 25", "기억 26", "기억 27", "기억 28", "기억 29"]


def test_chunk_limit_respects_pass(client, user_a):
    assert memory.chunk_limit_for({"memory_chunk_limit": None}) == MEMORY_FREE_CHUNKS
    assert memory.chunk_limit_for({"memory_chunk_limit": 60}) == 60
    # 패스로 산 한도가 무료 기본값보다 낮게 설정돼도 무료 수준은 보장
    assert memory.chunk_limit_for({"memory_chunk_limit": 5}) == MEMORY_FREE_CHUNKS


# ── 게이팅 해제 ─────────────────────────────────────────────────────────
def test_memory_is_open_to_everyone_during_cbt():
    from core.config import MEMORY_FOR_ALL
    assert MEMORY_FOR_ALL is True, (
        "CBT 에서 기억이 유료 게이팅되면 검증 대상 기능이 꺼진 채로 테스트하게 된다"
    )


# ── 계측 ────────────────────────────────────────────────────────────────
def test_events_are_recorded(client, user_a):
    uid = _uid(client, user_a)
    memory.log_event(uid, "evt-char", "sess-1", "extract", turn_count=10, value=2, detail="x")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM memory_events WHERE user_id = ? AND character_id = 'evt-char'", (uid,)
    ).fetchone()
    conn.close()
    assert row["event_type"] == "extract" and row["value"] == 2


def test_rating_reason_is_stored_and_logged(client, user_a):
    """'기억 못한다' 신고가 계측 스트림에 남아야 원인 분석이 가능하다."""
    uid = _uid(client, user_a)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO chat_history (session_id, character_id, user_id, role, content) "
        "VALUES ('sess-r', 'char-r', ?, 'assistant', '처음 뵙네요')", (uid,)
    )
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()

    r = client.post("/chat/rating", headers=auth(user_a), json={
        "session_id": "sess-r", "message_id": msg_id,
        "rating": "dislike", "reason": "memory",
    })
    assert r.status_code == 200, r.text
    assert r.json()["reason"] == "memory"

    conn = sqlite3.connect(DB_PATH)
    n = conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type = 'reported_forgot'"
    ).fetchone()[0]
    conn.close()
    assert n >= 1


def test_invalid_reason_is_ignored_not_500(client, user_a):
    uid = _uid(client, user_a)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO chat_history (session_id, character_id, user_id, role, content) "
        "VALUES ('sess-r2', 'char-r', ?, 'assistant', 'hi')", (uid,)
    )
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()

    r = client.post("/chat/rating", headers=auth(user_a), json={
        "session_id": "sess-r2", "message_id": msg_id,
        "rating": "dislike", "reason": "<script>",
    })
    assert r.status_code == 200
    assert r.json()["reason"] == ""


def test_memory_stats_endpoint(client, user_admin):
    r = client.get("/admin/memory-stats?days=7", headers=auth(user_admin))
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("sessions", "memory_book", "events", "forgot_reports", "feedback"):
        assert key in body


def test_memory_stats_requires_admin(client, user_a):
    assert client.get("/admin/memory-stats", headers=auth(user_a)).status_code == 403
