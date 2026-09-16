"""세션 캐시 크로스 유저 오염 테스트."""
from chat import session_store


def test_session_key_includes_user():
    a = session_store.make_key(1, "sess-1", "char-1")
    b = session_store.make_key(2, "sess-1", "char-1")
    assert a != b, "session_id 가 같아도 유저가 다르면 캐시가 분리돼야 한다"


def test_cache_roundtrip_and_drop():
    key = session_store.make_key(1, "s", "c")
    session_store.set(key, [{"role": "user", "content": "hi"}])
    assert session_store.get(key) == [{"role": "user", "content": "hi"}]
    assert session_store.drop(key) is True
    assert session_store.get(key) is None
