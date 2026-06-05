from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from chatbot import build_chain, ask, reset_session

chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    chain = build_chain()
    yield


app = FastAPI(title="LangChain Chatbot", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    session_id: str


@app.get("/")
def root():
    return {"status": "ok", "message": "POST a question to /chat"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        answer = await ask(chain, req.question, req.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return ChatResponse(answer=answer, session_id=req.session_id)


@app.post("/reset")
def reset(session_id: str = "default"):
    reset_session(session_id)
    return {"status": "ok", "cleared": session_id}