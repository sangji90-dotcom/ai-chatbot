"""Redis 백엔드 (있으면 사용, 없으면 프로세스 메모리로 폴백).

워커를 2개 이상 띄우는 순간 프로세스 메모리 기반 세션 캐시와 레이트리밋은
둘 다 무력화된다. REDIS_URL 만 넣으면 코드 수정 없이 공유 저장소로 전환되도록
여기서 한 겹 감싼다.
"""
import json
import logging
import os

logger = logging.getLogger("cache")

REDIS_URL = os.getenv("REDIS_URL", "").strip()

_client = None
_available = False

if REDIS_URL:
    try:
        import redis  # type: ignore

        _client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=1)
        _client.ping()
        _available = True
        logger.info("Redis 연결 성공 — 세션/레이트리밋을 공유 저장소로 사용합니다")
    except Exception as exc:  # noqa: BLE001
        # Redis 가 죽었다고 서비스가 죽으면 안 된다 — 메모리 폴백으로 계속 동작
        logger.warning("Redis 연결 실패(%s) — 인메모리 폴백으로 동작합니다", exc)
        _client = None
        _available = False


def available() -> bool:
    return _available and _client is not None


def _degrade(exc: Exception) -> None:
    global _available
    logger.warning("Redis 오류(%s) — 인메모리 폴백으로 전환", exc)
    _available = False


def get_json(key: str):
    if not available():
        return None
    try:
        raw = _client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:  # noqa: BLE001
        _degrade(exc)
        return None


def set_json(key: str, value, ttl: int) -> bool:
    if not available():
        return False
    try:
        _client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        return True
    except Exception as exc:  # noqa: BLE001
        _degrade(exc)
        return False


def delete(key: str) -> bool:
    if not available():
        return False
    try:
        return bool(_client.delete(key))
    except Exception as exc:  # noqa: BLE001
        _degrade(exc)
        return False


def incr_window(key: str, window: int) -> int | None:
    """고정 윈도우 카운터. 반환값이 None 이면 호출부가 메모리 폴백을 쓰면 된다."""
    if not available():
        return None
    try:
        pipe = _client.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, window)
        count, _ = pipe.execute()
        return int(count)
    except Exception as exc:  # noqa: BLE001
        _degrade(exc)
        return None
