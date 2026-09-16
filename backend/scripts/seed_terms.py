#!/usr/bin/env python3
"""약관·개인정보처리방침을 DB 에 적재한다.

terms 테이블은 "이용약관 내용을 입력해주세요." 라는 플레이스홀더 상태로 방치돼 있었다.
개인정보 국외이전 고지(대화 내용이 Google 로 전송됨)는 법적 필수 항목이다.

    python scripts/seed_terms.py           # seed/*.md 를 DB 에 반영
    python scripts/seed_terms.py --show    # 현재 DB 내용 확인
"""
import argparse
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from core.config import DB_PATH  # noqa: E402

FILES = {"terms": BASE / "seed" / "terms_ko.md",
         "privacy": BASE / "seed" / "privacy_ko.md"}


def show():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    for r in conn.execute("SELECT type, version, length(content) n, updated_at FROM terms"):
        head = conn.execute(
            "SELECT substr(content,1,60) h FROM terms WHERE type = ?", (r["type"],)
        ).fetchone()["h"].replace("\n", " ")
        print(f"[{r['type']:8s}] v{r['version']}  {r['n']:>6}자  {r['updated_at']}")
        print(f"           {head}...")
    conn.close()


def seed(version: str):
    conn = sqlite3.connect(DB_PATH)
    for kind, path in FILES.items():
        if not path.exists():
            print(f"[skip] {path} 없음")
            continue
        content = path.read_text(encoding="utf-8")
        conn.execute(
            """
            INSERT INTO terms (type, content, version, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(type) DO UPDATE
               SET content = excluded.content,
                   version = excluded.version,
                   updated_at = CURRENT_TIMESTAMP
            """,
            (kind, content, version),
        )
        print(f"[ok] {kind}: {len(content)}자 적재 (v{version})")
    conn.commit()
    conn.close()
    print("\n⚠️  시행일과 개인정보 보호책임자 연락처가 비어 있습니다.")
    print("    seed/*.md 에서 채운 뒤 이 스크립트를 다시 실행하세요.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--version", default="1.0")
    args = ap.parse_args()
    show() if args.show else seed(args.version)
