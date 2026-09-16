"""토큰 원장 서비스 — 지급/차감의 유일한 통로.

기존 구조의 문제와 대응:
1) read -> 판단 -> write 사이에 트랜잭션이 없어 동시 요청 시 이중 차감/무료 채팅이
   가능했다  -> 조건부 단일 UPDATE + rowcount 검사로 원자화.
2) token_balance 를 별도 컬럼으로 이중 관리해 실제 drift 가 발생했다
   -> balance 는 항상 (purchased + event) 파생값으로만 갱신.
3) 출석/광고/구매가 여러 커넥션에 걸쳐 있어 중복 지급이 가능했다
   -> idempotency_key 를 가진 token_grants 테이블로 중복 지급을 구조적으로 차단.
"""
from datetime import datetime, timedelta

from fastapi import HTTPException

from core.db import transaction

GOLD = "purchased"   # 구매 금화 (만료 1년)
SILVER = "event"     # 이벤트 은화 (만료 21일)
USE = "use"
EXPIRE = "expire"


class InsufficientTokens(HTTPException):
    def __init__(self):
        super().__init__(status_code=402, detail="토큰이 부족합니다.")


def _cur(db):
    """Connection 이 들어와도 Cursor 로 정규화한다.

    레거시 라우터들이 get_db() 로 받은 Connection 을 그대로 넘기는데,
    Connection 에는 rowcount 가 없어 원자성 검사가 조용히 깨진다.
    """
    return db.cursor() if hasattr(db, "cursor") else db


def grant(
    cur,
    user_id: int,
    amount: int,
    token_type: str,
    reason: str,
    expires_at=None,
    idempotency_key: str | None = None,
) -> bool:
    """토큰 지급. 이미 처리된 idempotency_key 면 아무것도 하지 않고 False.

    호출자가 연 트랜잭션 커서를 받는다 (지급과 상태 변경이 한 트랜잭션에 묶이도록).
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="지급 수량이 올바르지 않습니다.")

    cur = _cur(cur)
    if idempotency_key:
        cur.execute(
            """
            INSERT OR IGNORE INTO token_grants
                (idempotency_key, user_id, amount, token_type, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (idempotency_key, user_id, amount, token_type, reason),
        )
        if cur.rowcount == 0:
            return False  # 이미 지급됨 — 중복 요청

    column = "token_event" if token_type == SILVER else "token_purchased"
    cur.execute(
        f"""
        UPDATE users
           SET {column} = {column} + ?,
               token_balance = token_purchased + token_event + ?
         WHERE id = ?
        """,
        (amount, amount, user_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    cur.execute(
        """
        INSERT INTO token_history (user_id, amount, token_type, reason, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, token_type, reason, expires_at),
    )
    return True


def deduct(cur, user_id: int, amount: int, reason: str) -> int:
    """은화 우선 차감. 잔액 부족이면 402. 반환값은 차감 후 잔액.

    단일 UPDATE 로 처리하므로 동시 요청이 와도 잔액이 음수가 되지 않는다.
    (SQLite 는 UPDATE 의 우변을 모두 갱신 전 값으로 평가한다)
    """
    if amount <= 0:
        return 0

    cur = _cur(cur)
    cur.execute(
        """
        UPDATE users
           SET token_event     = MAX(0, token_event - ?),
               token_purchased = token_purchased - MAX(0, ? - token_event),
               token_balance   = token_purchased + token_event - ?
         WHERE id = ?
           AND token_purchased + token_event >= ?
        """,
        (amount, amount, amount, user_id, amount),
    )
    if cur.rowcount == 0:
        raise InsufficientTokens()

    cur.execute(
        """
        INSERT INTO token_history (user_id, amount, token_type, reason)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, -amount, USE, reason),
    )

    cur.execute("SELECT token_balance FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    return row["token_balance"] if row else 0


def refund(cur, user_id: int, amount: int, reason: str) -> None:
    """차감했지만 서비스 제공에 실패한 경우 되돌린다 (예: LLM 호출 실패)."""
    if amount <= 0:
        return
    cur = _cur(cur)
    cur.execute(
        """
        UPDATE users
           SET token_event   = token_event + ?,
               token_balance = token_purchased + token_event + ?
         WHERE id = ?
        """,
        (amount, amount, user_id),
    )
    cur.execute(
        """
        INSERT INTO token_history (user_id, amount, token_type, reason)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, amount, SILVER, f"환급: {reason}"),
    )


# ── 트랜잭션을 직접 여는 편의 래퍼 (라우터 밖에서 호출될 때) ──────────────
def grant_standalone(user_id: int, amount: int, token_type: str, reason: str,
                     expires_at=None, idempotency_key: str | None = None) -> bool:
    with transaction() as cur:
        return grant(cur, user_id, amount, token_type, reason, expires_at, idempotency_key)


def deduct_standalone(user_id: int, amount: int, reason: str) -> int:
    with transaction() as cur:
        return deduct(cur, user_id, amount, reason)


def balance_of(cur, user_id: int) -> dict:
    cur = _cur(cur)
    cur.execute(
        "SELECT token_purchased, token_event, token_balance FROM users WHERE id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return dict(row)


def silver_expiry(days: int = 21) -> datetime:
    return datetime.now() + timedelta(days=days)
