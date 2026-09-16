"""권한 경계 회귀 테스트.

여기 있는 케이스는 전부 리팩터링 전 코드에서 '통과하면 안 되는데 통과하던' 것들이다.
"""
import pytest

from tests.conftest import auth


# ── 1. 결제 검증 없이 토큰 지급되던 경로 ────────────────────────────────
def test_purchase_requires_admin(client, user_a):
    r = client.post("/tokens/purchase/1?target_user_id=1", headers=auth(user_a))
    assert r.status_code == 403, "일반 유저가 토큰 구매 엔드포인트를 호출할 수 있으면 안 된다"


def test_manual_grant_requires_admin(client, user_a):
    r = client.post("/purchases/manual",
                    json={"user_id": 1, "token_amount": 999999}, headers=auth(user_a))
    assert r.status_code == 403


def test_memory_pass_cash_requires_admin(client, user_a):
    r = client.post("/tokens/memory-pass/purchase-cash?target_user_id=1", headers=auth(user_a))
    assert r.status_code == 403


# ── 2. /chat 인증·권한 ──────────────────────────────────────────────────
def test_chat_requires_auth(client):
    r = client.post("/chat", json={"character_id": "x", "message": "hi", "session_id": "s1"})
    assert r.status_code == 401, "비로그인 대화가 가능하면 LLM 비용이 무제한 노출된다"


def test_chat_blocks_private_character_of_other_user(client, user_a, user_b):
    created = client.post("/characters", headers=auth(user_a), json={
        "name": "비밀이", "age": 25, "job": "개발자", "personality": "조용함",
        "likes": "커피", "dislikes": "소음", "speech_style": "담백",
        "visibility": "private",
    })
    assert created.status_code == 200, created.text
    cid = created.json()["id"]

    r = client.post("/chat", headers=auth(user_b),
                    json={"character_id": cid, "message": "안녕", "session_id": "s1"})
    assert r.status_code == 403, "남의 private 캐릭터로 대화할 수 있으면 안 된다"


def test_clear_chat_requires_auth(client):
    r = client.delete("/chat/somesession/somechar")
    assert r.status_code == 401


# ── 3. refresh 토큰으로 API 호출 우회 ───────────────────────────────────
def test_refresh_token_cannot_access_api(client, user_a):
    r = client.get("/users/me", headers={"Authorization": f"Bearer {user_a['refresh_token']}"})
    assert r.status_code == 401, "refresh 토큰(30일)으로 일반 API 를 호출할 수 있으면 안 된다"


# ── 4. 미성년 캐릭터 생성 차단 ──────────────────────────────────────────
def test_minor_character_rejected(client, user_a):
    r = client.post("/characters", headers=auth(user_a), json={
        "name": "미성년", "age": 12, "job": "학생", "personality": "밝음",
        "likes": "게임", "dislikes": "숙제", "speech_style": "반말",
    })
    assert r.status_code == 422


# ── 5. 관리자 전용 경로 ─────────────────────────────────────────────────
def test_admin_endpoints_blocked(client, user_a):
    assert client.get("/admin/stats", headers=auth(user_a)).status_code == 403
    assert client.get("/admin/users", headers=auth(user_a)).status_code == 403


# ── 6. 비밀번호 정책 ────────────────────────────────────────────────────
@pytest.mark.parametrize("pw", ["short", "12345678", "abcdefgh"])
def test_weak_password_rejected(client, pw):
    r = client.post("/auth/register",
                    json={"email": f"weak{pw}@example.com", "username": "weak", "password": pw})
    assert r.status_code == 422


# ── 7. 레이트리밋 동작 (플래그를 켜고 직접 검증) ────────────────────────
def test_rate_limiter_counts_and_expires():
    from core import middleware

    key = "test-ip:/auth/login"
    assert all(not middleware.is_rate_limited(key, 3, 60) for _ in range(3))
    assert middleware.is_rate_limited(key, 3, 60) is True, "한도 초과는 차단돼야 한다"


def test_client_ip_ignores_forged_header_without_trusted_proxy():
    from unittest.mock import Mock

    from core import middleware

    req = Mock()
    req.headers = {"X-Forwarded-For": "1.2.3.4", "CF-Connecting-IP": "5.6.7.8"}
    req.client = Mock(host="10.0.0.1")
    # TRUSTED_PROXY=none 이면 전달 헤더를 신뢰하지 않는다 (헤더 위조로 우회 불가)
    assert middleware.client_ip(req) == "10.0.0.1"
