import json
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import chatbot
import storage
from config import CORS_ORIGINS, DEBUG, MOCK, MODEL_NAME, VERSION
from runtime import (
    APIError,
    ContextMiddleware,
    METRICS,
    configure_logging,
    fail,
    ok,
    rate_limit,
    require_api_key,
)
from schemas import (
    ChatData,
    ChatRequest,
    Deleted,
    Envelope,
    Health,
    Metrics,
    SessionDetail,
    SessionList,
)

DESCRIPTION = (
    "A REST wrapper around a stateful LangChain chatbot. Every endpoint returns the same JSON "
    "envelope — success, data, error, meta — so clients parse one shape whatever happens."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    storage.init_db()
    chatbot.init_model()
    yield


app = FastAPI(title="Chatbot REST API", version=VERSION, description=DESCRIPTION, lifespan=lifespan)

app.add_middleware(ContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)


def guard(identity: str = Depends(require_api_key)) -> str:
    rate_limit(identity)
    return identity


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    headers = {}
    if exc.status == 429 and isinstance(exc.details, dict):
        headers["Retry-After"] = str(exc.details.get("retry_after_seconds", 60))
    return JSONResponse(
        status_code=exc.status,
        content=fail(request, exc.code, exc.message, exc.details),
        headers=headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    codes = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(request, codes.get(exc.status_code, "http_error"), str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in err["loc"][1:]) or "body", "problem": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=fail(request, "validation_error", "The request body failed validation.", details),
    )


@app.exception_handler(chatbot.ChatbotError)
async def chatbot_error_handler(request: Request, exc: chatbot.ChatbotError):
    return JSONResponse(status_code=502, content=fail(request, "upstream_error", str(exc)))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    message = str(exc) if DEBUG else "The server hit an unexpected error."
    return JSONResponse(status_code=500, content=fail(request, "internal_error", message))


@app.get("/healthz", response_model=Envelope[Health], tags=["system"])
async def healthz(request: Request):
    return ok(
        request,
        Health(
            status="ok",
            version=VERSION,
            model="mock" if MOCK else MODEL_NAME,
            mock=MOCK,
            uptime_seconds=METRICS.snapshot()["uptime_seconds"],
            sessions=len(storage.list_sessions()),
        ),
    )


@app.get("/v1/metrics", response_model=Envelope[Metrics], tags=["system"])
async def metrics(request: Request, identity: str = Depends(guard)):
    return ok(request, Metrics(**METRICS.snapshot()))


@app.post("/v1/chat", response_model=Envelope[ChatData], tags=["chat"])
async def chat(request: Request, body: ChatRequest, identity: str = Depends(guard)):
    session_id = body.session_id or uuid.uuid4().hex[:12]
    storage.ensure_session(session_id, identity)

    result = await chatbot.ask(session_id, body.message, body.system)
    METRICS.record_chat(result["usage"]["total_tokens"])

    return ok(request, ChatData(session_id=session_id, **result))


@app.post("/v1/chat/stream", tags=["chat"])
async def chat_stream(request: Request, body: ChatRequest, identity: str = Depends(guard)):
    session_id = body.session_id or uuid.uuid4().hex[:12]
    storage.ensure_session(session_id, identity)
    request_id = request.state.request_id

    async def events():
        yield json.dumps({"type": "start", "session_id": session_id, "request_id": request_id}) + "\n"
        try:
            async for token in chatbot.stream(session_id, body.message, body.system):
                yield json.dumps({"type": "token", "text": token}) + "\n"
        except chatbot.ChatbotError as exc:
            yield json.dumps({"type": "error", "code": "upstream_error", "message": str(exc)}) + "\n"
            return
        turn = len(storage.get_messages(session_id)) // 2
        METRICS.record_chat(0)
        yield json.dumps({"type": "end", "session_id": session_id, "turn": turn}) + "\n"

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
    )


@app.get("/v1/sessions", response_model=Envelope[SessionList], tags=["sessions"])
async def sessions(request: Request, identity: str = Depends(guard)):
    rows = storage.list_sessions()
    return ok(request, SessionList(sessions=rows, count=len(rows)))


@app.get("/v1/sessions/{session_id}", response_model=Envelope[SessionDetail], tags=["sessions"])
async def session_detail(request: Request, session_id: str, identity: str = Depends(guard)):
    if not storage.session_exists(session_id):
        raise APIError(404, "session_not_found", f"No session '{session_id}'.")
    messages = storage.get_messages(session_id)
    return ok(request, SessionDetail(session_id=session_id, message_count=len(messages), messages=messages))


@app.delete("/v1/sessions/{session_id}", response_model=Envelope[Deleted], tags=["sessions"])
async def delete_session(request: Request, session_id: str, identity: str = Depends(guard)):
    if not storage.delete_session(session_id):
        raise APIError(404, "session_not_found", f"No session '{session_id}'.")
    return ok(request, Deleted(session_id=session_id, deleted=True))