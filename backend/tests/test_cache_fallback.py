"""Redis 미설정/장애 시에도 서비스가 정상 동작해야 한다."""
from core import cache
from chat import session_store
from core import middleware


def test_cache_reports_unavailable_without_redis():
    # 테스트 환경엔 REDIS_URL 이 없다 — 폴백 경로가 선택돼야 한다
    assert cache.available() is False
    assert cache.get_json("any") is None
    assert cache.set_json("any", {"a": 1}, 10) is False
    assert cache.incr_window("any", 60) is None


def test_session_store_works_without_redis():
    key = session_store.make_key(99, "s-fallback", "c-fallback")
    session_store.set(key, [{"role": "user", "content": "hi"}])
    assert session_store.get(key)[0]["content"] == "hi"
    assert session_store.drop(key) is True


def test_rate_limit_works_without_redis():
    key = "fallback-ip:/auth/login"
    assert all(not middleware.is_rate_limited(key, 2, 60) for _ in range(2))
    assert middleware.is_rate_limited(key, 2, 60) is True
