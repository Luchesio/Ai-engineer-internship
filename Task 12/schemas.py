from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from config import MAX_MESSAGE_CHARS

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str
    timestamp: str
    duration_ms: float
    version: str


class ErrorBody(BaseModel):
    code: str = Field(..., description="Stable machine-readable code, e.g. rate_limited")
    message: str
    details: Any | None = None


class Envelope(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None
    meta: Meta


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_CHARS)
    session_id: str | None = Field(default=None, max_length=64)
    system: str | None = Field(default=None, max_length=2000)


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatData(BaseModel):
    reply: str
    session_id: str
    turn: int
    model: str
    usage: Usage


class Message(BaseModel):
    role: str
    content: str
    created_at: float


class SessionSummary(BaseModel):
    id: str
    created_at: float
    message_count: int
    last_message_at: float | None = None


class SessionList(BaseModel):
    sessions: list[SessionSummary]
    count: int


class SessionDetail(BaseModel):
    session_id: str
    message_count: int
    messages: list[Message]


class Deleted(BaseModel):
    session_id: str
    deleted: bool


class Health(BaseModel):
    status: str
    version: str
    model: str
    mock: bool
    uptime_seconds: float
    sessions: int


class Metrics(BaseModel):
    uptime_seconds: float
    requests_total: int
    requests_by_status: dict[str, int]
    requests_by_route: dict[str, int]
    errors_total: int
    chat_messages: int
    tokens_total: int
    average_latency_ms: float