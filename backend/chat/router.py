import io
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from chat import llm, memory, session_store
from chat.tagfilter import TagStripper
from core.config import (
    AUTO_SUMMARY_THRESHOLD,
    BASE_DIR,
    CHAT_COST_BY_LENGTH,
    CHAT_DEDUCT,
    chat_cost,
    MEMORY_EXTRACT_EVERY,
    MEMORY_FOR_ALL,
    REGENERATE_COST,
    RECENT_TURNS_KEPT as RECENT_TURNS,
)
from core.db import read_only, transaction
from deps import assert_character_access, get_current_user

router = APIRouter(prefix="/chat", tags=["대화"])

# 하위 호환: 기존 코드가 chat.router.client 를 import 한다
client = llm.client

OUTPUT_LENGTH = {"short": 300, "medium": 1000, "long": 2000}
MAX_MESSAGE_LEN = 4000

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    # nginx 등 리버스 프록시가 버퍼링하면 스트리밍 효과가 사라진다
    "X-Accel-Buffering": "no",
}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# safety_mode 는 유저가 설정에서 켜고 끌 수 있는데, 지금까지 대화 로직이
# 이 값을 한 번도 읽지 않았다. 켜도 아무 일이 없는 설정은 버그를 넘어 신뢰 문제다.
SAFETY_INSTRUCTION = """

[안전 모드 — 반드시 준수]
- 성적인 묘사, 노골적인 신체 묘사를 하지 않는다.
- 폭력·자해·범죄를 구체적으로 묘사하거나 미화하지 않는다.
- 혐오 표현과 차별적 발언을 하지 않는다.
- 유저가 위 내용을 요구하면 캐릭터를 유지한 채 자연스럽게 화제를 돌린다.
"""

TAG_INSTRUCTION = """
응답 마지막에 반드시 아래 형식으로 태그를 추가해줘. 태그는 대화 내용을 분석해서 결정해.

[EMOTION:태그] [SITUATION:태그]

감정 태그 옵션: neutral, happy, sad, angry, shy, surprised, love, embarrassed, crying, serious
상황 태그 옵션: default, indoor, outdoor, night, cafe, forest, rain, sunny, fantasy, dramatic

예시: [EMOTION:happy] [SITUATION:cafe]
"""

# 키워드 목록은 1차 필터일 뿐이다. 실질 방어는
#   (1) 캐릭터 생성 시 age >= 19 서버 검증  (characters/router.py)
#   (2) llm.SAFETY_SETTINGS
#   (3) 신고 -> 관리자 모더레이션 큐
# 세 가지이며, 이 목록만으로 막힌다고 가정하면 안 된다.
_HARMFUL_PATTERNS = [
    r"로\s*리", r"쇼\s*타", r"l\s*o\s*l\s*i", r"s\s*h\s*o\s*t\s*a",
    r"아동\s*(성|음란|포르노)", r"어린이\s*(성|음란)", r"미성년.{0,4}(성관계|성적|섹스)",
    r"초등학생.{0,6}(성|야한|벗)", r"유아.{0,4}(성|음란)",
]
_HARMFUL_RE = re.compile("|".join(_HARMFUL_PATTERNS), re.IGNORECASE)


def check_harmful_content(message: str) -> bool:
    normalized = re.sub(r"[\s​_.\-]+", "", message).lower()
    return bool(_HARMFUL_RE.search(message) or _HARMFUL_RE.search(normalized))


class ChatRequest(BaseModel):
    character_id: str
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LEN)
    session_id: str = Field(min_length=1, max_length=128)


# dislike 가 기억 문제인지 말투 문제인지 구분이 안 되면 기억 품질을 측정할 수 없다
RATING_REASONS = ("memory", "tone", "repetition", "offtopic", "quality", "other")


class RatingRequest(BaseModel):
    session_id: str
    message_id: int
    rating: str
    reason: str = ""   # dislike 일 때만 의미 있음. RATING_REASONS 참고


class OocRequest(BaseModel):
    session_id: str
    character_id: str
    message_id: int
    new_content: str = Field(min_length=1, max_length=MAX_MESSAGE_LEN)


# ── 내부 헬퍼 ───────────────────────────────────────────────────────────
def _load_history(user_id: int, session_id: str, character_id: str) -> list:
    key = session_store.make_key(user_id, session_id, character_id)
    cached = session_store.get(key)
    if cached is not None:
        return cached

    with read_only() as cur:
        cur.execute(
            """
            SELECT id, role, content FROM chat_history
             WHERE session_id = ? AND character_id = ? AND user_id = ? AND role != 'system'
             ORDER BY id ASC
            """,
            (session_id, character_id, user_id),
        )
        history = [{"id": r["id"], "role": r["role"], "content": r["content"]} for r in cur.fetchall()]

    session_store.set(key, history)
    return history


def _build_context_block(user: dict, character_id: str) -> tuple[str, int]:
    """(system 에 붙일 블록, 주입된 기억 개수) 를 돌려준다."""
    user_id = user["id"]
    with read_only() as cur:
        cur.execute(
            "SELECT content FROM user_notes WHERE user_id = ? AND character_id = ? ORDER BY id ASC",
            (user_id, character_id),
        )
        notes = cur.fetchall()
        cur.execute(
            "SELECT name, content FROM user_personas WHERE user_id = ? AND character_id = ? ORDER BY id ASC",
            (user_id, character_id),
        )
        personas = cur.fetchall()

    # memory_chunk_limit 이 결제에만 쓰이고 주입 시엔 무제한이었다.
    # 상한을 실제로 걸어 프롬프트가 무한히 커지는 것을 막는다 (최신 우선).
    limit = memory.chunk_limit_for(user)
    memories = memory.load_memories(user_id, character_id, limit)

    block = ""
    if notes:
        block += "\n\n[유저 기본 정보 — 자연스럽게 반영하되 직접 언급 금지]\n"
        block += "\n".join(f"- {n['content']}" for n in notes)
    if personas:
        block += "\n\n[유저 캐릭터 설정 — 롤플레잉에 적극 반영]\n"
        block += "\n".join(
            f"- {p['name']}: {p['content']}" if p["name"] else f"- {p['content']}" for p in personas
        )
    if memories:
        block += "\n\n[중요 기억 — 반드시 기억하고 대화에 반영]\n"
        block += "\n".join(f"- {m['content']}" for m in memories)
    return block, len(memories)


def _to_contents(history: list) -> list:
    return [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
        for m in history
    ]


async def auto_summarize(history: list, character_name: str) -> list:
    old_history, recent_history = history[:-RECENT_TURNS], history[-RECENT_TURNS:]
    history_text = "\n".join(
        f"{'유저' if m['role'] == 'user' else character_name}: {m['content']}" for m in old_history
    )
    response = await llm.generate(
        [{"role": "user", "parts": [{"text": history_text}]}],
        system_instruction="""
이전 대화를 핵심만 추출해서 메모리 패스 형식으로 요약해줘.

형식:
[관계] 유저와 캐릭터의 현재 관계
[주요 사건] 중요한 사건 3개 이하
[감정 흐름] 현재 감정 상태
[약속/결정] 중요한 약속이나 결정사항
[기타 기억] 기억해야 할 세부 정보

5줄 이내로 간결하게.
""",
        max_output_tokens=300,
        apply_safety=False,
    )
    summary = llm.text_of(response)
    return [
        {"role": "user", "content": f"[메모리 패스 - 이전 대화 핵심 기억]\n{summary}"},
        {"role": "assistant", "content": "네, 이전 내용을 기억하고 있어요."},
        *recent_history,
    ]


async def extract_memory(user_id: int, character_id: str, session_id: str,
                         recent_turns: list, character_name: str) -> int:
    """직전 구간 전체를 보고 새 기억만 뽑아 저장한다.

    이전 구현은 10번째 턴의 (질문, 답변) 한 쌍만 넘겨서 그 사이 9턴은 버려졌다.
    이미 저장된 기억을 프롬프트에 함께 줘서 같은 내용이 계속 쌓이는 것도 막는다.
    """
    known = memory.load_memories(user_id, character_id, memory.MEMORY_FREE_CHUNKS)
    system, body = memory.build_extract_prompt(recent_turns, character_name, known)

    result = await llm.generate(
        [{"role": "user", "parts": [{"text": body}]}],
        system_instruction=system,
        max_output_tokens=200,
        apply_safety=False,
    )
    items = memory.parse_extracted(llm.text_of(result), known)
    saved = memory.save_memories(user_id, character_id, items)

    memory.log_event(
        user_id, character_id, session_id,
        "extract" if saved else "extract_empty",
        turn_count=len(recent_turns), value=saved,
        detail=" | ".join(items),
    )
    return saved


# ── 대화 ────────────────────────────────────────────────────────────────
# ── 대화 파이프라인 ─────────────────────────────────────────────────────
# chat / stream / regenerate 가 같은 절차를 공유하도록 준비·마무리를 분리한다.

@dataclass
class Turn:
    """LLM 호출에 필요한 것들을 한 번에 들고 다니는 컨텍스트."""
    uid: int
    character: dict
    char_name: str
    session_id: str
    character_id: str
    key: str
    working: list          # 이번 호출에 넣을 히스토리
    system_instruction: str
    max_tokens: int
    charged: int           # 차감한 토큰 (실패 시 이만큼 환급)
    safety: bool = True    # 유저의 safety_mode 설정


async def _prepare_turn(current_user: dict, character_id: str, session_id: str,
                        user_message: str | None, cost: int) -> Turn:
    """권한 검사 → 기억 주입 → 토큰 차감 → 히스토리 구성.

    user_message 가 None 이면 재생성이다 (새 유저 발화를 추가하지 않음).
    """
    from tokens.router import deduct_token

    uid = current_user["id"]
    character = assert_character_access(character_id, current_user)
    char_name = character["name"]

    key = session_store.make_key(uid, session_id, character_id)
    history = _load_history(uid, session_id, character_id)

    with read_only() as cur:
        cur.execute(
            "SELECT output_length, output_multiplier, safety_mode FROM users WHERE id = ?", (uid,)
        )
        u = cur.fetchone()
    output_length = u["output_length"] if u else "medium"
    base_tokens = OUTPUT_LENGTH.get(output_length, 1000)
    multiplier = (u["output_multiplier"] if u and u["output_multiplier"] else 1.0)
    max_tokens = int(base_tokens * multiplier)
    safety_on = bool(u["safety_mode"]) if u else True

    # cost < 0 이면 유저의 출력 길이 설정에 따라 자동 산정한다
    if cost < 0:
        cost = chat_cost(output_length)

    # 차감은 LLM 호출 전에. 실패하면 Turn.charged 만큼 환급한다.
    if cost > 0:
        deduct_token(uid, cost, f"{char_name}와 대화")

    context_block, injected = _build_context_block(current_user, character_id)
    memory.log_event(uid, character_id, session_id, "inject",
                     turn_count=len(history), value=injected)

    working = history + ([{"role": "user", "content": user_message}] if user_message else [])

    if len(working) > AUTO_SUMMARY_THRESHOLD:
        before = len(working)
        try:
            working = await auto_summarize(working, char_name)
            memory.log_event(uid, character_id, session_id, "summarize",
                             turn_count=before, value=len(working))
        except HTTPException as exc:
            # 요약 실패는 대화를 막지 않지만, 조용히 넘기면 기억 손실 원인을 못 찾는다
            memory.log_event(uid, character_id, session_id, "summarize_fail",
                             turn_count=before, detail=str(exc.detail))

    system_instruction = character["prompt"] + context_block
    if safety_on:
        system_instruction += SAFETY_INSTRUCTION

    return Turn(
        uid=uid, character=character, char_name=char_name,
        session_id=session_id, character_id=character_id, key=key,
        working=working,
        system_instruction=system_instruction,
        max_tokens=max_tokens, charged=cost, safety=safety_on,
    )


def _refund(turn: Turn) -> None:
    """서비스 제공에 실패했으면 차감분을 되돌린다."""
    from core import token_service as ts
    if turn.charged <= 0:
        return
    with transaction() as cur:
        ts.refund(cur, turn.uid, turn.charged, f"{turn.char_name}와 대화 실패")


async def _finalize_turn(turn: Turn, user_message: str | None, assistant_message: str,
                         replaced_message_id: int | None = None) -> int:
    """응답 저장 + 카운터 + 캐시 갱신 + 업적 + 기억 추출. message_id 반환."""
    from achievements.router import check_and_grant

    uid, cid, sid = turn.uid, turn.character_id, turn.session_id

    with transaction() as cur:
        user_msg_id = None
        if replaced_message_id is not None:
            # 재생성: 기존 응답을 교체한다 (히스토리에 중복 응답을 쌓지 않음)
            cur.execute(
                "UPDATE chat_history SET content = ? WHERE id = ? AND user_id = ?",
                (assistant_message, replaced_message_id, uid),
            )
            message_id = replaced_message_id
        else:
            if user_message is not None:
                cur.execute(
                    "INSERT INTO chat_history (session_id, character_id, user_id, role, content) "
                    "VALUES (?, ?, ?, 'user', ?)",
                    (sid, cid, uid, user_message),
                )
                user_msg_id = cur.lastrowid
            cur.execute(
                "INSERT INTO chat_history (session_id, character_id, user_id, role, content) "
                "VALUES (?, ?, ?, 'assistant', ?)",
                (sid, cid, uid, assistant_message),
            )
            message_id = cur.lastrowid
            cur.execute(
                "UPDATE characters SET chat_count = chat_count + 1 WHERE id = ?", (cid,)
            )

        cur.execute(
            "SELECT COUNT(*) AS cnt FROM chat_history WHERE user_id = ? AND role = 'user'", (uid,)
        )
        total = cur.fetchone()["cnt"]
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM chat_history "
            " WHERE user_id = ? AND character_id = ? AND role = 'user'", (uid, cid),
        )
        single = cur.fetchone()["cnt"]

    # 캐시 갱신
    working = turn.working
    if replaced_message_id is not None:
        for item in reversed(working):
            if item.get("role") == "assistant":
                item["content"] = assistant_message
                item["id"] = replaced_message_id
                break
    else:
        if user_message is not None:
            for item in reversed(working):
                if item.get("role") == "user" and item.get("content") == user_message:
                    item["id"] = user_msg_id
                    break
        working.append({"id": message_id, "role": "assistant", "content": assistant_message})
    session_store.set(turn.key, working)

    # 재생성은 업적·기억 추출을 다시 돌리지 않는다 (같은 턴이므로)
    if replaced_message_id is not None:
        return message_id

    if len(working) % MEMORY_EXTRACT_EVERY == 0:
        allowed = MEMORY_FOR_ALL
        if not allowed:
            with read_only() as cur:
                cur.execute("SELECT memory_pass_expires_at FROM users WHERE id = ?", (uid,))
                row = cur.fetchone()
            expires = row["memory_pass_expires_at"] if row else None
            if expires:
                try:
                    allowed = datetime.fromisoformat(expires) > datetime.now()
                except ValueError:
                    allowed = False
        if allowed:
            try:
                await extract_memory(uid, cid, sid, working[-MEMORY_EXTRACT_EVERY:], turn.char_name)
            except HTTPException as exc:
                memory.log_event(uid, cid, sid, "extract_fail",
                                 turn_count=len(working), detail=str(exc.detail))

    for threshold, code in ((1, "first_chat"), (10, "chat_10"), (50, "chat_50"),
                            (100, "chat_100"), (500, "chat_500"), (1000, "chat_1000")):
        if total == threshold:
            check_and_grant(uid, code)
    for threshold, code in ((10, "chat_single_10"), (50, "chat_single_50"), (100, "chat_single_100")):
        if single == threshold:
            check_and_grant(uid, code)

    return message_id


async def _run_llm(turn: Turn) -> str:
    """비스트리밍 생성 + MAX_TOKENS 이어쓰기 1회."""
    contents = _to_contents(turn.working)
    response = await llm.generate(contents, turn.system_instruction + TAG_INSTRUCTION,
                                  turn.max_tokens, apply_safety=turn.safety)
    raw = llm.text_of(response)

    finish = None
    if getattr(response, "candidates", None):
        finish = getattr(response.candidates[0].finish_reason, "name", None)
    if finish == "MAX_TOKENS":
        cont = await llm.generate(
            contents + [
                {"role": "model", "parts": [{"text": raw}]},
                {"role": "user", "parts": [{"text": "(이어서 작성)"}]},
            ],
            turn.system_instruction + TAG_INSTRUCTION,
            turn.max_tokens, apply_safety=turn.safety,
        )
        raw += llm.text_of(cont)

    if not raw.strip():
        raise HTTPException(status_code=502, detail="AI가 응답을 생성하지 못했어요. 다시 시도해주세요.")
    return raw


def _split_tags(raw: str) -> tuple[str, str, str]:
    emotion = re.search(r"\[EMOTION:(\w+)\]", raw)
    situation = re.search(r"\[SITUATION:(\w+)\]", raw)
    message = re.sub(r"\[EMOTION:\w+\]\s*|\[SITUATION:\w+\]\s*", "", raw).strip()
    return (message,
            emotion.group(1) if emotion else "neutral",
            situation.group(1) if situation else "default")


async def _handle_summary_command(turn_user: dict, character_id: str, session_id: str,
                                  char_name: str, key: str, history: list):
    """'요약!' 명령 처리. 요약 대상이 부족하면 None 을 돌려준다."""
    if len(history) < 4:
        return {"character": char_name, "message": "아직 요약할 대화가 충분하지 않아요."}
    history_text = "\n".join(
        f"{'유저' if m['role'] == 'user' else char_name}: {m['content']}" for m in history
    )
    response = await llm.generate(
        [{"role": "user", "parts": [{"text": history_text}]}],
        system_instruction="지금까지의 대화 내용을 간결하게 요약해줘. 중요한 사건, 감정, 결정만 남기고 압축해줘. 3~5문장으로.",
        max_output_tokens=500,
        apply_safety=False,
    )
    summary = llm.text_of(response)
    session_store.set(key, [
        {"role": "user", "content": f"[이전 대화 요약]\n{summary}"},
        {"role": "assistant", "content": "네, 이전 내용을 기억하고 있어요. 계속 이야기해요."},
    ])
    with transaction() as cur:
        cur.execute(
            "INSERT INTO chat_history (session_id, character_id, user_id, role, content) "
            "VALUES (?, ?, ?, 'system', ?)",
            (session_id, character_id, turn_user["id"], f"[요약]\n{summary}"),
        )
    return {"character": char_name, "message": f"📝 대화를 요약했어요!\n\n{summary}"}


@router.post("", summary="대화하기")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """인증 필수. 이전에는 get_optional_user 라 비로그인도 토큰 차감 없이
    Gemini 를 호출할 수 있었고(비용 무제한 노출), private/성인 캐릭터 검사도 없었다."""
    uid = current_user["id"]
    character = assert_character_access(request.character_id, current_user)
    char_name = character["name"]

    if check_harmful_content(request.message):
        return {"character": char_name, "message": "해당 내용은 생성할 수 없어요."}

    if request.message.strip() == "요약!":
        key = session_store.make_key(uid, request.session_id, request.character_id)
        history = _load_history(uid, request.session_id, request.character_id)
        return await _handle_summary_command(
            current_user, request.character_id, request.session_id, char_name, key, history
        )

    turn = await _prepare_turn(current_user, request.character_id, request.session_id,
                               request.message, cost=-1)
    try:
        raw = await _run_llm(turn)
    except HTTPException:
        _refund(turn)
        raise

    message, emotion, situation = _split_tags(raw)
    message_id = await _finalize_turn(turn, request.message, message)

    return {
        "character": char_name,
        "message": message,
        "message_id": message_id,
        "emotion": emotion,
        "situation": situation,
        "cost": turn.charged,
    }


class RegenerateRequest(BaseModel):
    character_id: str
    session_id: str = Field(min_length=1, max_length=128)


@router.post("/regenerate", summary="응답 재생성")
async def regenerate(request: RegenerateRequest,
                     current_user: dict = Depends(get_current_user)):
    """마지막 AI 응답을 버리고 다시 생성한다.

    캐릭터챗에서 마음에 안 드는 응답이 나왔을 때 유저의 선택지는
    '재생성' 아니면 '이탈' 인데, 지금까지는 재생성이 없어 이탈뿐이었다.

    재생성은 불만 신호이기도 하므로 계측에 남긴다.
    """
    uid = current_user["id"]

    # 마지막 assistant 메시지를 찾는다
    with read_only() as cur:
        cur.execute(
            """
            SELECT id, role FROM chat_history
             WHERE user_id = ? AND character_id = ? AND session_id = ? AND role != 'system'
             ORDER BY id DESC LIMIT 1
            """,
            (uid, request.character_id, request.session_id),
        )
        last = cur.fetchone()

    if not last or last["role"] != "assistant":
        raise HTTPException(status_code=400, detail="재생성할 응답이 없어요.")
    target_id = last["id"]

    # REGENERATE_COST 를 명시적으로 0 으로 둔 경우는 무료, 아니면 길이별 요금을 따른다
    regen_cost = 0 if REGENERATE_COST == 0 else -1
    turn = await _prepare_turn(current_user, request.character_id, request.session_id,
                               None, regen_cost)

    # 마지막 assistant 응답을 빼고 같은 맥락으로 다시 요청한다
    if turn.working and turn.working[-1].get("role") == "assistant":
        turn.working = turn.working[:-1]
    if not turn.working:
        _refund(turn)
        raise HTTPException(status_code=400, detail="재생성할 응답이 없어요.")

    try:
        raw = await _run_llm(turn)
    except HTTPException:
        _refund(turn)
        raise

    message, emotion, situation = _split_tags(raw)
    # working 끝에 assistant 를 다시 붙여야 _finalize_turn 이 교체 대상을 찾는다
    turn.working.append({"id": target_id, "role": "assistant", "content": message})
    await _finalize_turn(turn, None, message, replaced_message_id=target_id)

    memory.log_event(uid, request.character_id, request.session_id,
                     "regenerated", turn_count=len(turn.working),
                     detail=f"message_id={target_id}")

    return {
        "character": turn.char_name,
        "message": message,
        "message_id": target_id,
        "emotion": emotion,
        "situation": situation,
    }


@router.post("/stream", summary="대화하기 (스트리밍)")
async def chat_stream(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """SSE 로 응답을 흘려보낸다.

    비스트리밍은 완성까지 3~10초 동안 빈 화면이라 체감 이탈이 크다.
    이벤트: delta(조각) / done(저장 결과) / error
    """
    uid = current_user["id"]
    character = assert_character_access(request.character_id, current_user)
    char_name = character["name"]

    if check_harmful_content(request.message):
        async def blocked():
            yield _sse("delta", {"text": "해당 내용은 생성할 수 없어요."})
            yield _sse("done", {"message_id": None, "emotion": "neutral", "situation": "default"})
        return StreamingResponse(blocked(), media_type="text/event-stream", headers=_SSE_HEADERS)

    if request.message.strip() == "요약!":
        key = session_store.make_key(uid, request.session_id, request.character_id)
        history = _load_history(uid, request.session_id, request.character_id)
        result = await _handle_summary_command(
            current_user, request.character_id, request.session_id, char_name, key, history
        )

        async def summarized():
            yield _sse("delta", {"text": result["message"]})
            yield _sse("done", {"message_id": None, "emotion": "neutral", "situation": "default"})
        return StreamingResponse(summarized(), media_type="text/event-stream", headers=_SSE_HEADERS)

    # 토큰 차감은 스트림 시작 전에 — 부족하면 여기서 402 가 나가야 한다
    turn = await _prepare_turn(current_user, request.character_id, request.session_id,
                               request.message, cost=-1)

    async def event_stream():
        stripper = TagStripper()
        try:
            async for chunk in llm.generate_stream(
                _to_contents(turn.working), turn.system_instruction + TAG_INSTRUCTION,
                turn.max_tokens, apply_safety=turn.safety,
            ):
                safe = stripper.feed(chunk)
                if safe:
                    yield _sse("delta", {"text": safe})
            tail = stripper.flush()
            if tail:
                yield _sse("delta", {"text": tail})
        except HTTPException as exc:
            _refund(turn)
            yield _sse("error", {"detail": exc.detail, "refunded": turn.charged})
            return
        except Exception:  # noqa: BLE001
            logging.getLogger("chat").exception("stream failed")
            _refund(turn)
            yield _sse("error", {"detail": "AI 응답 생성에 실패했어요.", "refunded": turn.charged})
            return

        message = stripper.clean_text()
        if not message:
            _refund(turn)
            yield _sse("error", {"detail": "AI가 응답을 생성하지 못했어요.", "refunded": turn.charged})
            return

        emotion, situation = stripper.tags()
        try:
            message_id = await _finalize_turn(turn, request.message, message)
        except Exception:  # noqa: BLE001
            logging.getLogger("chat").exception("finalize failed")
            yield _sse("error", {"detail": "응답 저장에 실패했어요."})
            return

        yield _sse("done", {
            "message_id": message_id,
            "emotion": emotion,
            "situation": situation,
            "character": char_name,
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/rating", summary="메시지 평가")
def rate_message(request: RatingRequest, current_user: dict = Depends(get_current_user)):
    if request.rating not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="rating은 like 또는 dislike만 가능합니다.")
    reason = request.reason if request.reason in RATING_REASONS else ""

    with transaction() as cur:
        # 남의 메시지에 평가를 남기지 못하도록 소유권 확인
        cur.execute(
            "SELECT id FROM chat_history WHERE id = ? AND user_id = ?",
            (request.message_id, current_user["id"]),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")
        cur.execute(
            "INSERT OR REPLACE INTO message_ratings "
            "  (user_id, session_id, message_id, rating, reason) "
            "VALUES (?, ?, ?, ?, ?)",
            (current_user["id"], request.session_id, request.message_id,
             request.rating, reason),
        )
        cur.execute(
            "SELECT character_id FROM chat_history WHERE id = ?", (request.message_id,)
        )
        row = cur.fetchone()

    if reason == "memory" and row:
        # "얘 아까 말한 거 까먹었는데" 를 계측 스트림에 직접 남긴다
        memory.log_event(current_user["id"], row["character_id"], request.session_id,
                         "reported_forgot", detail=f"message_id={request.message_id}")

    return {"message": "평가 완료", "reason": reason}


@router.get("/rating/reasons", summary="평가 사유 목록")
def get_rating_reasons():
    return [
        {"code": "memory", "label": "앞서 한 얘기를 기억 못해요"},
        {"code": "repetition", "label": "같은 말을 반복해요"},
        {"code": "tone", "label": "말투가 캐릭터랑 안 맞아요"},
        {"code": "offtopic", "label": "엉뚱한 소리를 해요"},
        {"code": "quality", "label": "답변이 너무 짧거나 성의 없어요"},
        {"code": "other", "label": "기타"},
    ]


@router.patch("/ooc", summary="OOC 수정")
def ooc_edit(request: OocRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["id"]
    with transaction() as cur:
        cur.execute(
            "UPDATE chat_history SET content = ? WHERE id = ? AND user_id = ?",
            (request.new_content, request.message_id, uid),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    # 캐시 반영: 기존 구현은 히스토리에 넣은 적 없는 msg["id"] 로 매칭해
    # 항상 실패했고, DB만 바뀌고 AI 컨텍스트는 옛 내용을 계속 참조했다.
    key = session_store.make_key(uid, request.session_id, request.character_id)
    history = session_store.get(key)
    if history:
        for msg in history:
            if msg.get("id") == request.message_id:
                msg["content"] = request.new_content
                session_store.set(key, history)
                break
        else:
            session_store.drop(key)  # 못 찾으면 캐시를 버려 다음 요청에 DB에서 재적재
    return {"message": "메시지 수정 완료"}


@router.post("/new/{character_id}", summary="새 채팅 시작")
def new_chat(character_id: str, session_id: str, current_user: dict = Depends(get_current_user)):
    session_store.drop(session_store.make_key(current_user["id"], session_id, character_id))
    return {"message": "새 채팅 시작 완료"}


@router.get("/resume/{character_id}", summary="대화 이어하기")
def resume_chat(character_id: str, session_id: str, current_user: dict = Depends(get_current_user)):
    assert_character_access(character_id, current_user)
    uid = current_user["id"]
    with read_only() as cur:
        cur.execute(
            """
            SELECT id, role, content, created_at FROM chat_history
             WHERE session_id = ? AND character_id = ? AND user_id = ?
             ORDER BY id ASC
            """,
            (session_id, character_id, uid),
        )
        rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        return {"history": [], "message": "이전 대화 없음"}

    session_store.set(
        session_store.make_key(uid, session_id, character_id),
        [{"id": r["id"], "role": r["role"], "content": r["content"]}
         for r in rows if r["role"] != "system"],
    )
    return {"history": rows, "message": f"대화 {len(rows)}개 복원 완료"}


@router.get("/sessions/{character_id}", summary="캐릭터 세션 목록")
def get_sessions(character_id: str, current_user: dict = Depends(get_current_user)):
    with read_only() as cur:
        cur.execute(
            """
            -- FE 는 started_at / last_at 을 읽는데 서버가 last_chat 만 줘서
            -- 세션 목록의 날짜가 "Invalid Date" 로 표시되고 있었다.
            SELECT session_id,
                   MIN(created_at) AS started_at,
                   MAX(created_at) AS last_at,
                   MAX(created_at) AS last_chat,   -- 기존 필드명 호환
                   COUNT(*) AS message_count
              FROM chat_history
             WHERE character_id = ? AND user_id = ? AND role = 'user'
             GROUP BY session_id
             ORDER BY last_at DESC
            """,
            (character_id, current_user["id"]),
        )
        return [dict(r) for r in cur.fetchall()]


@router.get("/history/{character_id}", summary="대화 기록 조회")
def get_chat_history(character_id: str, session_id: str | None = None,
                     limit: int = 200, current_user: dict = Depends(get_current_user)):
    limit = min(max(1, limit), 1000)
    sql = """SELECT id, role, content, created_at FROM chat_history
              WHERE character_id = ? AND user_id = ?"""
    params: list = [character_id, current_user["id"]]
    if session_id:
        sql += " AND session_id = ?"
        params.append(session_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with read_only() as cur:
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    return list(reversed(rows))


@router.delete("/{session_id}/{character_id}", summary="대화 초기화")
def clear_chat(session_id: str, character_id: str,
               current_user: dict = Depends(get_current_user)):
    """이전에는 인증 의존성 자체가 없어 아무나 남의 세션 캐시를 지울 수 있었다."""
    session_store.drop(session_store.make_key(current_user["id"], session_id, character_id))
    return {"message": "대화 기록 삭제 완료"}


@router.get("/export/{character_id}", summary="대화 PDF 내보내기")
def export_chat_pdf(character_id: str, session_id: str,
                    current_user: dict = Depends(get_current_user)):
    assert_character_access(character_id, current_user)
    with read_only() as cur:
        cur.execute(
            """
            SELECT role, content, created_at FROM chat_history
             WHERE session_id = ? AND character_id = ? AND user_id = ?
             ORDER BY id ASC
            """,
            (session_id, character_id, current_user["id"]),
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT name FROM characters WHERE id = ?", (character_id,))
        char = cur.fetchone()

    if not rows:
        raise HTTPException(status_code=404, detail="대화 기록이 없습니다.")

    char_name = char["name"] if char else character_id
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    font_name = "Helvetica"
    font_path = os.path.join(BASE_DIR, "NanumGothic-Regular.ttf")
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
        font_name = "NanumGothic"

    c.setFont(font_name, 16)
    c.drawString(50, height - 50, f"{char_name}와의 대화")
    c.setFont(font_name, 9)
    c.drawString(50, height - 70, f"세션: {session_id}  |  총 {len(rows)}개 메시지")

    y, line_height, margin = height - 100, 16, 50
    max_width = width - margin * 2

    def wrap(text: str) -> list[str]:
        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for ch in paragraph:
                if c.stringWidth(line + ch, font_name, 9) > max_width:
                    lines.append(line)
                    line = ch
                else:
                    line += ch
            lines.append(line)
        return lines

    for row in rows:
        if row["role"] == "system":
            continue
        label = "나" if row["role"] == "user" else char_name
        color = (0.1, 0.4, 0.8) if row["role"] == "user" else (0.1, 0.6, 0.3)
        if y < 100:
            c.showPage()
            y = height - 50
        c.setFillColorRGB(*color)
        c.setFont(font_name, 10)
        c.drawString(margin, y, f"[{label}]  {str(row['created_at'])[:16]}")
        y -= line_height
        c.setFillColorRGB(0, 0, 0)
        c.setFont(font_name, 9)
        for line in wrap(row["content"]):
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont(font_name, 9)
            c.drawString(margin + 10, y, line)
            y -= line_height
        y -= 8

    c.save()
    buffer.seek(0)

    # 한글 파일명은 RFC 5987 로 인코딩해야 한다 (raw 삽입 시 헤더가 깨짐)
    filename = f"{char_name}_대화_{session_id[:8]}.pdf"
    disposition = f"attachment; filename=\"chat.pdf\"; filename*=UTF-8''{quote(filename)}"
    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": disposition})
