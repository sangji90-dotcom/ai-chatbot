"""캐릭터 기억(memory_book) 추출·주입.

기존 구현의 문제 세 가지를 여기서 정리한다.

1) 추출이 메모리 패스 보유자 전용이었다
   -> CBT 에서는 검증 대상 기능이 꺼진 채로 테스트하게 된다. MEMORY_FOR_ALL 로 연다.

2) "10턴마다 추출" 이라면서 실제로는 10번째 턴의 1쌍만 LLM 에 넘겼다
   -> 유저가 5턴째에 말한 이름은 영영 기록되지 않았다. 직전 구간 전체를 넘긴다.

3) memory_chunk_limit 이 결제에만 쓰이고 주입 시 LIMIT 이 없었다
   -> 대화가 길어질수록 프롬프트가 무한히 커지고, 오래된 기억이 최신을 밀어냈다.
      최신 우선으로 상한을 건다.
"""
import logging
import re

from core.config import (
    MEMORY_FREE_CHUNKS,
    MEMORY_MAX_PER_EXTRACT,
)
from core.db import read_only, transaction

logger = logging.getLogger("memory")

EXTRACT_SYSTEM = """이전 대화에서 앞으로 기억해야 할 정보만 뽑아줘.

기억할 가치가 있는 것:
- 유저의 이름, 호칭, 나이, 직업, 사는 곳
- 관계의 변화 (호칭이 바뀜, 고백, 다툼과 화해)
- 약속한 것, 결정한 것
- 감정적으로 중요했던 사건
- 유저가 반복해서 언급한 취향이나 습관

기억할 가치가 없는 것:
- 인사말, 잡담, 일회성 농담
- 캐릭터가 한 말 (유저에 대한 정보가 아님)
- 이미 알고 있는 정보 (아래 목록에 있는 것)

규칙:
- 한 줄에 하나씩, 최대 {max_items}개
- 각 줄은 40자 이내의 평서문
- 기억할 것이 없으면 정확히 "없음" 한 단어만 출력
- 설명이나 번호를 붙이지 말 것

[이미 기억하고 있는 것]
{known}
"""


def _normalize(text: str) -> str:
    return re.sub(r"[\s.,!?~…]+", "", text).lower()


def log_event(user_id: int, character_id: str, session_id: str,
              event_type: str, turn_count: int = 0, value: int = 0, detail: str = "") -> None:
    """계측은 실패해도 대화를 막지 않는다."""
    try:
        with transaction() as cur:
            cur.execute(
                """
                INSERT INTO memory_events
                    (user_id, character_id, session_id, event_type, turn_count, value, detail)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, character_id, session_id, event_type, turn_count, value, detail[:500]),
            )
    except Exception:  # noqa: BLE001
        logger.warning("memory_event 기록 실패 (%s)", event_type, exc_info=True)


def chunk_limit_for(user: dict) -> int:
    """주입 상한. 패스 보유자는 구매한 만큼, 그 외에는 무료 기본값."""
    limit = user.get("memory_chunk_limit")
    if limit:
        return max(int(limit), MEMORY_FREE_CHUNKS)
    return MEMORY_FREE_CHUNKS


def load_memories(user_id: int, character_id: str, limit: int) -> list[dict]:
    """최신 우선으로 상한만큼 가져와, 주입 시에는 시간순으로 되돌린다."""
    with read_only() as cur:
        cur.execute(
            """
            SELECT id, title, content FROM memory_book
             WHERE user_id = ? AND character_id = ?
             ORDER BY id DESC LIMIT ?
            """,
            (user_id, character_id, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
    return list(reversed(rows))


def total_count(user_id: int, character_id: str) -> int:
    with read_only() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM memory_book WHERE user_id = ? AND character_id = ?",
            (user_id, character_id),
        )
        return cur.fetchone()["cnt"]


def build_extract_prompt(recent_turns: list, character_name: str, known: list[dict]) -> tuple[str, str]:
    """(system_instruction, 대화 본문) 을 만든다."""
    known_text = "\n".join(f"- {m['content']}" for m in known) or "(아직 없음)"
    system = EXTRACT_SYSTEM.format(max_items=MEMORY_MAX_PER_EXTRACT, known=known_text)
    body = "\n".join(
        f"{'유저' if m['role'] == 'user' else character_name}: {m['content']}"
        for m in recent_turns
    )
    return system, body


def parse_extracted(text: str, known: list[dict]) -> list[str]:
    """LLM 출력에서 새 기억만 골라낸다 (중복·빈값 제거)."""
    text = (text or "").strip()
    if not text or text.replace(".", "").strip() == "없음":
        return []

    known_norm = {_normalize(m["content"]) for m in known}
    results: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        line = re.sub(r"^[-*·\d]+[.)]?\s*", "", line).strip()
        if not line or line == "없음" or len(line) > 120:
            continue
        norm = _normalize(line)
        if not norm or norm in known_norm:
            continue
        known_norm.add(norm)
        results.append(line)
        if len(results) >= MEMORY_MAX_PER_EXTRACT:
            break
    return results


def save_memories(user_id: int, character_id: str, items: list[str]) -> int:
    if not items:
        return 0
    with transaction() as cur:
        for content in items:
            cur.execute(
                "INSERT INTO memory_book (user_id, character_id, title, content) "
                "VALUES (?, ?, '자동추출', ?)",
                (user_id, character_id, content),
            )
    return len(items)
