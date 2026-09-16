"""파티챗 AI 진행자.

기존 WebSocket 은 'start' 에 안내 문구만 뱉고 끝이었다. 스토리를 골라 방을
만들어도 AI 가 아무것도 하지 않아 파티챗은 사실상 단체 채팅이었다.

여기서는 스토리(또는 캐릭터)의 system_prompt 를 바탕으로 AI 가 장면을 열고,
멤버들의 발화가 쌓이면 이어서 서사를 진행한다.
"""
import logging

from core.db import read_only
from chat import llm

logger = logging.getLogger("party")

# 멤버 발화가 이만큼 쌓이면 AI 가 한 번 진행한다.
# 매 발화마다 돌리면 비용과 대기가 커지고, 너무 늦으면 대화가 붕 뜬다.
TURNS_BEFORE_NARRATION = 3
CONTEXT_MESSAGES = 30

NARRATOR_RULES = """

[진행 규칙]
- 너는 이 이야기의 진행자다. 특정 플레이어를 대신해 말하지 않는다.
- 플레이어들의 행동을 받아 장면을 전개하고, 결과를 묘사한다.
- 3~5문장으로 짧게. 장황한 묘사보다 다음 행동을 유도하는 상황 제시가 중요하다.
- 마지막에 플레이어들이 무엇을 할 수 있는지 자연스럽게 열어둔다.
- 특정 한 명에게만 말을 걸지 말고 파티 전체를 향해 서술한다.
"""


def load_scene(room: dict) -> tuple[str, str]:
    """(system_instruction, 장면 제목) — 스토리 우선, 없으면 캐릭터."""
    with read_only() as cur:
        if room["story_id"]:
            cur.execute("SELECT * FROM stories WHERE id = ?", (room["story_id"],))
            story = cur.fetchone()
            if story:
                return (
                    f"{story['system_prompt']}\n\n[배경]\n{story['background']}" + NARRATOR_RULES,
                    story["title"],
                )
        if room["character_id"]:
            cur.execute("SELECT * FROM characters WHERE id = ?", (room["character_id"],))
            char = cur.fetchone()
            if char:
                return (
                    f"{char['prompt']}\n\n너는 여러 명의 플레이어와 동시에 대화한다."
                    + NARRATOR_RULES,
                    char["name"],
                )
    # 스토리도 캐릭터도 없는 방 — 자유 진행
    return (
        "너는 즉흥 이야기의 진행자다. 플레이어들이 만들어가는 상황을 받아 "
        "장면을 전개한다." + NARRATOR_RULES,
        "자유 진행",
    )


def recent_context(room_id: int, limit: int = CONTEXT_MESSAGES) -> list[dict]:
    with read_only() as cur:
        cur.execute(
            """
            SELECT pm.message_type, pm.content, u.username
              FROM party_messages pm
              LEFT JOIN users u ON pm.user_id = u.id
             WHERE pm.room_id = ?
             ORDER BY pm.id DESC LIMIT ?
            """,
            (room_id, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
    return list(reversed(rows))


def _to_contents(rows: list[dict]) -> list[dict]:
    """파티 로그를 LLM 대화 형식으로. 진행자 발언만 model 역할."""
    contents = []
    for r in rows:
        if r["message_type"] == "narration":
            contents.append({"role": "model", "parts": [{"text": r["content"]}]})
        else:
            name = r.get("username") or "플레이어"
            contents.append({"role": "user", "parts": [{"text": f"{name}: {r['content']}"}]})
    return contents


async def open_scene(room: dict) -> str:
    """방 시작 시 첫 장면을 연다."""
    system, title = load_scene(room)
    response = await llm.generate(
        [{"role": "user", "parts": [{"text":
            "파티가 모였다. 이야기의 첫 장면을 열어라. "
            "상황을 제시하고 플레이어들이 무엇을 할 수 있을지 보여줘라."}]}],
        system_instruction=system,
        max_output_tokens=int(600 * (room["output_multiplier"] or 1.0)),
    )
    return llm.text_of(response).strip()


async def advance(room: dict) -> str:
    """누적된 플레이어 행동을 받아 이야기를 진행한다."""
    system, _ = load_scene(room)
    rows = recent_context(room["id"])
    if not rows:
        return await open_scene(room)

    contents = _to_contents(rows)
    contents.append({"role": "user", "parts": [{"text":
        "위 플레이어들의 행동을 반영해 이야기를 이어가라."}]})

    response = await llm.generate(
        contents,
        system_instruction=system,
        max_output_tokens=int(600 * (room["output_multiplier"] or 1.0)),
    )
    return llm.text_of(response).strip()
