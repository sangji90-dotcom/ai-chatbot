#!/usr/bin/env python3
"""데이터 정합성 점검 — 배포 후/정기 실행용.

토큰 잔액 drift 는 실제로 발생했던 문제다. 조용히 다시 벌어지지 않게 감시한다.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import DB_PATH  # noqa: E402

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
problems = []

rows = conn.execute("""
    SELECT id, token_balance, token_purchased, token_event FROM users
     WHERE token_balance != token_purchased + token_event
""").fetchall()
if rows:
    problems.append(f"토큰 잔액 불일치 {len(rows)}건: {[dict(r) for r in rows[:5]]}")

rows = conn.execute(
    "SELECT id FROM users WHERE token_purchased < 0 OR token_event < 0"
).fetchall()
if rows:
    problems.append(f"음수 토큰 보유 {len(rows)}건: {[r['id'] for r in rows[:5]]}")

rows = conn.execute("""
    SELECT COUNT(*) AS cnt FROM chat_history ch
     WHERE ch.character_id NOT IN (SELECT id FROM characters)
""").fetchone()
if rows["cnt"]:
    problems.append(f"고아 chat_history {rows['cnt']}건 (삭제된 캐릭터 참조)")

rows = conn.execute("""
    SELECT COUNT(*) AS cnt FROM character_likes
     WHERE character_id NOT IN (SELECT id FROM characters)
""").fetchone()
if rows["cnt"]:
    problems.append(f"고아 character_likes {rows['cnt']}건")

fk = conn.execute("PRAGMA foreign_key_check").fetchall()
if fk:
    problems.append(f"FK 위반 {len(fk)}건")

integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
if integrity != "ok":
    problems.append(f"DB 무결성 이상: {integrity}")

conn.close()

if problems:
    print("[문제 발견]")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("정합성 점검 통과")
