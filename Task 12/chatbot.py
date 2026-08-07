import asyncio
import os
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import storage
from config import (
    DEFAULT_SYSTEM_PROMPT,
    HISTORY_WINDOW,
    MOCK,
    MODEL_NAME,
    REQUEST_TIMEOUT,
    TEMPERATURE,
)

_model = None


class ChatbotError(RuntimeError):
    pass


def init_model():
    global _model
    if MOCK:
        _model = None
        return
    if not os.getenv("OPENAI_API_KEY"):
        raise ChatbotError("OPENAI_API_KEY is not set. Set it, or start the API with MOCK=1.")

    from langchain_openai import ChatOpenAI

    _model = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE, timeout=REQUEST_TIMEOUT)


def _build_messages(session_id: str, message: str, system: str | None) -> list:
    messages = [SystemMessage(system or DEFAULT_SYSTEM_PROMPT)]
    for row in storage.get_messages(session_id, limit=HISTORY_WINDOW):
        messages.append(
            HumanMessage(row["content"]) if row["role"] == "user" else AIMessage(row["content"])
        )
    messages.append(HumanMessage(message))
    return messages


def _mock_reply(session_id: str, message: str) -> str:
    turns = len(storage.get_messages(session_id)) // 2 + 1
    return f"[mock] Turn {turns} in session {session_id}. You said: {message.strip()}"


def _usage(reply: AIMessage | None, message: str, text: str) -> dict:
    meta = getattr(reply, "usage_metadata", None) if reply else None
    if meta:
        return {
            "prompt_tokens": meta.get("input_tokens", 0),
            "completion_tokens": meta.get("output_tokens", 0),
            "total_tokens": meta.get("total_tokens", 0),
        }
    prompt = max(len(message) // 4, 1)
    completion = max(len(text) // 4, 1)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion}


async def ask(session_id: str, message: str, system: str | None = None) -> dict:
    if MOCK:
        text = _mock_reply(session_id, message)
        reply = None
    else:
        try:
            reply = await _model.ainvoke(_build_messages(session_id, message, system))
        except asyncio.TimeoutError as exc:
            raise ChatbotError(f"Upstream model timed out after {REQUEST_TIMEOUT}s") from exc
        except Exception as exc:
            raise ChatbotError(f"Upstream model call failed: {exc}") from exc
        text = reply.content

    storage.add_message(session_id, "user", message)
    storage.add_message(session_id, "assistant", text)

    return {
        "reply": text,
        "model": "mock" if MOCK else MODEL_NAME,
        "usage": _usage(reply, message, text),
        "turn": len(storage.get_messages(session_id)) // 2,
    }


async def stream(session_id: str, message: str, system: str | None = None) -> AsyncIterator[str]:
    parts: list[str] = []

    if MOCK:
        for word in _mock_reply(session_id, message).split(" "):
            parts.append(word + " ")
            yield word + " "
            await asyncio.sleep(0.02)
    else:
        try:
            async for chunk in _model.astream(_build_messages(session_id, message, system)):
                if chunk.content:
                    parts.append(chunk.content)
                    yield chunk.content
        except Exception as exc:
            raise ChatbotError(f"Upstream model stream failed: {exc}") from exc

    text = "".join(parts).strip()
    storage.add_message(session_id, "user", message)
    storage.add_message(session_id, "assistant", text)