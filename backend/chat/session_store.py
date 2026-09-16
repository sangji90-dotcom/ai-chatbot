"""채팅 세션 히스토리 캐시.

기존 구현은 모듈 전역 dict 에 `f"{session_id}_{character_id}"` 를 키로 썼다.
키에 user_id 가 없어 다른 유저의 session_id 를 알면 그 대화 맥락을 이어받을 수
있었고(크로스 유저 오염), 만료가 없어 메모리가 무한히 증가했다.

여기서는 user_id 를 키에 포함하고 TTL + LRU 상한을 둔다.
멀티 프로세스로 넘어가면 이 모듈만 Redis 구현으로 교체하면 된다.
"""
import threading
import time
from collections import OrderedDict

from core import cache
from core.config import SESSION_CACHE_MAX, SESSION_CACHE_TTL_SEC

_REDIS_PREFIX = "stellia:sess:"

_lock = threading.Lock()
_store: "OrderedDict[str, tuple[float, list]]" = OrderedDict()


def make_key(user_id: int | None, session_id: str, character_id: str) -> str:
    # 비로그인은 캐시를 공유하지 않도록 별도 네임스페이스
    owner = str(user_id) if user_id else "anon"
    return f"{owner}:{session_id}:{character_id}"


def _evict_locked() -> None:
    now = time.time()
    expired = [k for k, (ts, _) in _store.items() if now - ts > SESSION_CACHE_TTL_SEC]
    for k in expired:
        _store.pop(k, None)
    while len(_store) > SESSION_CACHE_MAX:
        _store.popitem(last=False)


def get(key: str) -> list | None:
    if cache.available():
        value = cache.get_json(_REDIS_PREFIX + key)
        if value is not None:
            return value
        # Redis 에 없으면 메모리도 확인 (전환 직후 과도기)
    with _lock:
        item = _store.get(key)
        if not item:
            return None
        ts, history = item
        if time.time() - ts > SESSION_CACHE_TTL_SEC:
            _store.pop(key, None)
            return None
        _store.move_to_end(key)
        return history


def set(key: str, history: list) -> None:
    if cache.set_json(_REDIS_PREFIX + key, history, SESSION_CACHE_TTL_SEC):
        return
    with _lock:
        _store[key] = (time.time(), history)
        _store.move_to_end(key)
        _evict_locked()


def drop(key: str) -> bool:
    removed = cache.delete(_REDIS_PREFIX + key)
    with _lock:
        return _store.pop(key, None) is not None or removed


def size() -> int:
    with _lock:
        return len(_store)
