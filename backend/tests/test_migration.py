"""마이그레이션 회귀 테스트.

실제 DB 에서 party_members / party_messages 의 FK 가 DROP 된 party_rooms_old 를
가리킨 채 남아 있었다. FK 를 켜는 순간 방 생성·입장이 전부 실패하는 상태였다.
"""
import sqlite3
import tempfile
from pathlib import Path


def _build_broken_db(path: str) -> None:
    """ALTER TABLE RENAME 이 자식 FK 를 바꿔버리는 상황을 그대로 재현한다."""
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT);
        CREATE TABLE characters (id TEXT PRIMARY KEY);
        CREATE TABLE stories (id INTEGER PRIMARY KEY AUTOINCREMENT);
        CREATE TABLE party_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            story_id INTEGER,
            character_id TEXT,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE party_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            character_stats TEXT NOT NULL,
            is_ready INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES party_rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        INSERT INTO users (email) VALUES ('a@b.c');
        INSERT INTO party_rooms (code, host_id) VALUES ('ABC123', 1);
    """)
    # 여기서 자식 테이블의 FK 참조명이 party_rooms_old 로 바뀐다
    conn.execute("ALTER TABLE party_rooms RENAME TO party_rooms_old")
    conn.execute("""
        CREATE TABLE party_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            story_id INTEGER,
            character_id TEXT,
            host_id INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            max_members INTEGER DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("INSERT INTO party_rooms SELECT * FROM party_rooms_old")
    conn.execute("DROP TABLE party_rooms_old")
    conn.commit()
    conn.close()


def test_broken_fk_blocks_insert_then_gets_repaired():
    from database import _clean_orphan_rows, _repair_dangling_fk_references

    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "broken.db")
        _build_broken_db(path)

        # 복구 전: FK 를 켜면 party_members INSERT 가 실패한다
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute(
                "INSERT INTO party_members (room_id, user_id, character_stats) VALUES (1, 1, '{}')"
            )
            conn.close()
            raise AssertionError("깨진 FK 상태에서 INSERT 가 성공하면 재현이 안 된 것")
        except sqlite3.OperationalError as exc:
            assert "party_rooms_old" in str(exc)
        conn.rollback()

        # 복구
        cur = conn.cursor()
        _repair_dangling_fk_references(cur, conn)
        _clean_orphan_rows(cur, conn)
        conn.commit()

        # 복구 후: 정상 동작 + FK 위반 0
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO party_members (room_id, user_id, character_stats) VALUES (1, 1, '{}')"
        )
        conn.commit()
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

        sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name='party_members'"
        ).fetchone()[0]
        assert "party_rooms_old" not in sql
        conn.close()


def test_party_room_create_and_join_works(client, user_a, user_b):
    """FK 활성화 상태에서 방 생성/입장이 실제로 되는지 (위 버그의 사용자 관점 증상)."""
    created = client.post("/party/rooms", headers={"Authorization": f"Bearer {user_a['access_token']}"},
                          json={"max_members": 4})
    assert created.status_code == 200, created.text
    code = created.json()["code"]

    joined = client.post("/party/rooms/join", headers={"Authorization": f"Bearer {user_b['access_token']}"},
                         json={"code": code, "character_stats": {}})
    assert joined.status_code == 200, joined.text
