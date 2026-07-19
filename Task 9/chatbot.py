import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import storage

load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
HISTORY_WINDOW = int(os.getenv("HISTORY_WINDOW", "20"))

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. You remember what the user has told you "
    "earlier in this conversation and use it to answer follow-up questions."
)


def build_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. See README for setup.")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    model = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    return prompt | model | StrOutputParser()


def load_history(session_id: str) -> list:
    rows = storage.get_messages(session_id, limit=HISTORY_WINDOW)
    return [
        HumanMessage(row["content"]) if row["role"] == "human" else AIMessage(row["content"])
        for row in rows
    ]


async def ask(chain, question: str, session_id: str) -> str:
    storage.ensure_session(session_id)
    history = load_history(session_id)
    answer = await chain.ainvoke({"question": question, "history": history})
    storage.add_message(session_id, "human", question)
    storage.add_message(session_id, "ai", answer)
    return answer