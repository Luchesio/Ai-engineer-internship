import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from tools import TOOLS

load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to live weather and currency tools. "
    "Call a tool whenever the user asks about the current weather or exchange rates, "
    "then answer clearly and concisely. Never invent numbers you did not get from a tool."
)

_history: dict[str, list] = {}
_tools_by_name = {t.name: t for t in TOOLS}


def build_model():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. See README for setup.")
    return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE).bind_tools(TOOLS)


async def ask(model, question: str, session_id: str) -> str:
    history = _history.setdefault(session_id, [SystemMessage(SYSTEM_PROMPT)])
    history.append(HumanMessage(question))

    ai = await model.ainvoke(history)
    history.append(ai)

    while ai.tool_calls:
        for call in ai.tool_calls:
            result = await _tools_by_name[call["name"]].ainvoke(call["args"])
            history.append(ToolMessage(result, tool_call_id=call["id"]))
        ai = await model.ainvoke(history)
        history.append(ai)

    return ai.content


def reset_session(session_id: str) -> None:
    _history.pop(session_id, None)