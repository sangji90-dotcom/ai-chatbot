#!/usr/bin/env python3
"""SQLite 온라인 백업.

파일을 그냥 cp 하면 WAL 모드에서 쓰기 중인 트랜잭션과 겹쳐 깨진 사본이 나온다.
sqlite3 의 backup API 는 서비스를 멈추지 않고 일관된 스냅샷을 만든다.

    python scripts/backup_db.py            # backups/ 에 저장, 14일치 보관
    python scripts/backup_db.py --keep 30 --out /data/backups
"""
import argparse
import gzip
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import DB_PATH  # noqa: E402


def backup(out_dir: Path, keep_days: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = out_dir / f"chatbot-{stamp}.db"

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(target)
    try:
        # 5페이지씩 복사하며 중간에 쓰기를 양보한다 (서비스 정지 없음)
        src.backup(dst, pages=5, progress=lambda *_: time.sleep(0))
    finally:
        dst.close()
        src.close()

    gz = target.with_suffix(".db.gz")
    with open(target, "rb") as f_in, gzip.open(gz, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    target.unlink()

    # 무결성 확인 — 깨진 백업을 성공으로 보고하지 않는다
    check = sqlite3.connect(DB_PATH).execute("PRAGMA integrity_check").fetchone()[0]
    if check != "ok":
        raise SystemExit(f"[FATAL] 원본 DB 무결성 이상: {check}")

    cutoff = datetime.now() - timedelta(days=keep_days)
    removed = 0
    for old in out_dir.glob("chatbot-*.db.gz"):
        if datetime.fromtimestamp(old.stat().st_mtime) < cutoff:
            old.unlink()
            removed += 1

    print(f"백업 완료: {gz} ({gz.stat().st_size / 1024:.0f}KB), 오래된 백업 {removed}개 삭제")
    return gz


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "backups"))
    ap.add_argument("--keep", type=int, default=14, help="보관 일수")
    args = ap.parse_args()
    backup(Path(args.out), args.keep)
