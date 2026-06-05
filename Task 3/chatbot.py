import os
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

_history: dict[str, list] = {}


def build_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. See README for setup.")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful, concise assistant. Answer the user's questions clearly."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    model = ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    return prompt | model | StrOutputParser()


async def ask(chain, question: str, session_id: str) -> str:
    history = _history.setdefault(session_id, [])
    answer = await chain.ainvoke({"question": question, "history": history})
    history.extend([HumanMessage(question), AIMessage(answer)])
    return answer


def reset_session(session_id: str) -> None:
    _history.pop(session_id, None)