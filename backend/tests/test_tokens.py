"""토큰 원장 정합성 / 동시성 테스트."""
import sqlite3
import threading

from core import token_service as ts
from core.config import DB_PATH
from core.db import transaction
from tests.conftest import auth


def _balance(uid):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT token_purchased, token_event, token_balance FROM users WHERE id = ?", (uid,)
    ).fetchone()
    conn.close()
    return dict(row)


def _uid(client, tok):
    return client.get("/users/me", headers=auth(tok)).json()["id"]


def test_balance_always_matches_components(client, user_a):
    uid = _uid(client, user_a)
    with transaction() as cur:
        ts.grant(cur, uid, 500, ts.GOLD, "test-grant")
        ts.deduct(cur, uid, 200, "test-deduct")
    b = _balance(uid)
    assert b["token_balance"] == b["token_purchased"] + b["token_event"]


def test_deduct_never_goes_negative(client, user_a):
    uid = _uid(client, user_a)
    b = _balance(uid)
    total = b["token_purchased"] + b["token_event"]
    try:
        with transaction() as cur:
            ts.deduct(cur, uid, total + 1, "over-deduct")
        raise AssertionError("잔액 초과 차감이 성공하면 안 된다")
    except ts.InsufficientTokens:
        pass
    after = _balance(uid)
    assert after["token_purchased"] >= 0 and after["token_event"] >= 0


def test_idempotency_blocks_double_grant(client, user_a):
    uid = _uid(client, user_a)
    before = _balance(uid)["token_balance"]
    for _ in range(3):
        with transaction() as cur:
            ts.grant(cur, uid, 1000, ts.SILVER, "dup", idempotency_key=f"dup-test:{uid}")
    after = _balance(uid)["token_balance"]
    assert after - before == 1000, "같은 멱등키로는 한 번만 지급돼야 한다"


def test_concurrent_deduct_does_not_overspend(client, user_a):
    """동시 차감 — 예전 구현(read->판단->write)에서는 이중 차감이 났다."""
    uid = _uid(client, user_a)
    with transaction() as cur:
        cur.execute(
            "UPDATE users SET token_purchased = 0, token_event = 1000, token_balance = 1000 "
            "WHERE id = ?", (uid,)
        )

    results = []

    def worker():
        try:
            with transaction() as cur:
                ts.deduct(cur, uid, 300, "concurrent")
            results.append("ok")
        except Exception:
            results.append("fail")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    b = _balance(uid)
    assert b["token_event"] >= 0
    assert b["token_balance"] == b["token_purchased"] + b["token_event"]
    assert results.count("ok") <= 3, f"1000토큰으로 300씩 3회를 초과 차감했다: {results}"


def test_attendance_twice_rejected(client, user_a):
    first = client.post("/tokens/attendance", headers=auth(user_a))
    assert first.status_code == 200, first.text
    second = client.post("/tokens/attendance", headers=auth(user_a))
    assert second.status_code == 400, "하루 두 번 출석 보상이 나가면 안 된다"
