"""SQLite 커넥션 + 트랜잭션 경계.

기존 코드는 라우터마다 get_db() -> commit() -> close() 를 흩어 놓아
- 예외 경로에서 커넥션이 새고
- 읽고-판단-쓰기 사이에 원자성이 없었다.
transaction() 컨텍스트 매니저로 두 문제를 동시에 닫는다.
"""
import sqlite3
from contextlib import contextmanager

from core.config import DB_PATH

_INIT_DONE = False


def _configure(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    # FK 제약은 커넥션마다 켜야 실제로 동작한다 (기존에는 전혀 적용되지 않았음)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    _configure(conn)
    return conn


@contextmanager
def transaction():
    """with transaction() as cur:  — 블록을 정상 통과하면 commit, 예외면 rollback.

    어느 경로로 빠져나가도 커넥션은 반드시 닫힌다.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def read_only():
    """조회 전용. 커밋하지 않고 커넥션만 확실히 반납한다."""
    conn = get_db()
    try:
        yield conn.cursor()
    finally:
        conn.close()
