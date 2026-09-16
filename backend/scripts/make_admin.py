#!/usr/bin/env python3
"""최초 관리자 지정.

관리자 권한 부여 API 는 관리자만 호출할 수 있어서, 첫 관리자는 여기서 만든다.

    python scripts/make_admin.py you@example.com
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import DB_PATH  # noqa: E402

if len(sys.argv) != 2:
    raise SystemExit("사용법: python scripts/make_admin.py <email>")

email = sys.argv[1]
conn = sqlite3.connect(DB_PATH)
cur = conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
conn.commit()
if cur.rowcount == 0:
    conn.close()
    raise SystemExit(f"해당 이메일의 계정이 없습니다: {email}")
conn.close()
print(f"{email} 을 관리자로 지정했습니다.")
