"""Gemini 호출 래퍼.

기존에는 async def 라우터 안에서 동기 generate_content() 를 호출해
응답 3~10초 동안 이벤트 루프 전체가 멈췄다(동시 접속 2명이면 두 번째 유저는
앞 사람이 끝날 때까지 대기). 여기서 비동기 경로를 강제한다.
"""
import asyncio
import logging

from fastapi import HTTPException
from google import genai

from core.config import GEMINI_API_KEY

logger = logging.getLogger("llm")
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = "gemini-2.5-flash"

# 미성년자 성적 묘사 차단은 프롬프트 문구가 아니라 모델 안전설정으로도 이중으로 건다
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


# safety_mode 를 꺼도 유지되는 최소 안전선
MINIMUM_SAFETY = [
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


async def generate(contents, system_instruction: str, max_output_tokens: int,
                   apply_safety: bool = True, timeout: float = 60.0):
    config = {
        "system_instruction": system_instruction,
        "max_output_tokens": max_output_tokens,
    }
    # apply_safety=False 여도 아동 관련은 절대 풀지 않는다.
    # 유저 설정(safety_mode)으로 조절되는 것은 성인 표현 수위이지, 아동 보호가 아니다.
    config["safety_settings"] = SAFETY_SETTINGS if apply_safety else MINIMUM_SAFETY

    try:
        aio = getattr(client, "aio", None)
        if aio is not None:
            coro = aio.models.generate_content(model=MODEL, contents=contents, config=config)
        else:
            # SDK 버전이 낮아 aio 가 없으면 최소한 스레드풀로 빼서 루프는 살린다
            coro = asyncio.to_thread(
                client.models.generate_content, model=MODEL, contents=contents, config=config
            )
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("LLM timeout")
        raise HTTPException(status_code=504, detail="응답이 지연되고 있어요. 다시 시도해주세요.")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail="AI 응답 생성에 실패했어요. 잠시 후 다시 시도해주세요.") from exc


async def generate_stream(contents, system_instruction: str, max_output_tokens: int,
                          apply_safety: bool = True):
    """청크 단위로 텍스트를 yield 한다.

    SSE 로 흘려보내기 위한 경로. 실패는 호출부가 토큰 환급을 할 수 있도록
    HTTPException 으로 올린다.
    """
    config = {
        "system_instruction": system_instruction,
        "max_output_tokens": max_output_tokens,
    }
    config["safety_settings"] = SAFETY_SETTINGS if apply_safety else MINIMUM_SAFETY

    aio = getattr(client, "aio", None)
    if aio is None:
        # SDK 가 비동기 스트리밍을 지원하지 않으면 한 번에 받아 통째로 넘긴다
        response = await generate(contents, system_instruction, max_output_tokens, apply_safety)
        yield text_of(response)
        return

    try:
        stream = await aio.models.generate_content_stream(
            model=MODEL, contents=contents, config=config
        )
        async for chunk in stream:
            piece = text_of(chunk)
            if piece:
                yield piece
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM stream failed")
        raise HTTPException(
            status_code=502, detail="AI 응답 생성에 실패했어요. 잠시 후 다시 시도해주세요."
        ) from exc


def text_of(response) -> str:
    """안전 필터로 차단되면 response.text 가 None 이다. 호출부가 터지지 않게 정규화."""
    try:
        text = response.text
    except Exception:  # noqa: BLE001
        text = None
    return text or ""
