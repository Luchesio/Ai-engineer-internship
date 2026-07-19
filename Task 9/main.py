import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import storage
from chatbot import build_chain, ask, HISTORY_WINDOW

chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    storage.init_db()
    chain = build_chain()
    yield


app = FastAPI(title="Stateful Chatbot with Session History", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    turns_in_session: int


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "POST a question to /chat. Omit session_id to start a new session.",
        "history_window": HISTORY_WINDOW,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or uuid.uuid4().hex[:12]
    try:
        answer = await ask(chain, req.question, session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    turns = len(storage.get_messages(session_id)) // 2
    return ChatResponse(answer=answer, session_id=session_id, turns_in_session=turns)


@app.get("/sessions")
def sessions():
    return {"sessions": storage.list_sessions()}


@app.get("/sessions/{session_id}/history")
def history(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail=f"No session '{session_id}'")
    return {"session_id": session_id, "messages": storage.get_messages(session_id)}


@app.delete("/sessions/{session_id}")
def delete(session_id: str):
    if not storage.delete_session(session_id):
        raise HTTPException(status_code=404, detail=f"No session '{session_id}'")
    return {"status": "ok", "deleted": session_id}