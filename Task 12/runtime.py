import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Header, Request
from starlette.middleware.base import BaseHTTPMiddleware

from config import API_KEYS, RATE_LIMIT_PER_MINUTE, VERSION
from schemas import ErrorBody, Meta

logger = logging.getLogger("chatbot_api")


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class Metrics:
    def __init__(self):
        self.started = time.time()
        self.requests_total = 0
        self.by_status: dict[str, int] = {}
        self.by_route: dict[str, int] = {}
        self.errors_total = 0
        self.chat_messages = 0
        self.tokens_total = 0
        self.latency_sum = 0.0

    def record(self, route: str, status: int, duration_ms: float) -> None:
        self.requests_total += 1
        self.by_status[str(status)] = self.by_status.get(str(status), 0) + 1
        self.by_route[route] = self.by_route.get(route, 0) + 1
        self.latency_sum += duration_ms
        if status >= 400:
            self.errors_total += 1

    def record_chat(self, tokens: int) -> None:
        self.chat_messages += 1
        self.tokens_total += tokens

    def snapshot(self) -> dict:
        return {
            "uptime_seconds": round(time.time() - self.started, 1),
            "requests_total": self.requests_total,
            "requests_by_status": self.by_status,
            "requests_by_route": self.by_route,
            "errors_total": self.errors_total,
            "chat_messages": self.chat_messages,
            "tokens_total": self.tokens_total,
            "average_latency_ms": round(self.latency_sum / self.requests_total, 1)
            if self.requests_total
            else 0.0,
        }


METRICS = Metrics()
_windows: dict[str, tuple[int, int]] = {}


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request.state.started = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - request.state.started) * 1000, 2)
        route = request.scope.get("route").path if request.scope.get("route") else request.url.path
        METRICS.record(route, response.status_code, duration_ms)

        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        logger.info(
            json.dumps(
                {
                    "request_id": request.state.request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )
        return response


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> str:
    if not API_KEYS:
        return f"anon:{request.client.host if request.client else 'unknown'}"
    if not x_api_key:
        raise APIError(401, "missing_api_key", "Provide your key in the X-API-Key header.")
    if x_api_key not in API_KEYS:
        raise APIError(401, "invalid_api_key", "That API key is not recognised.")
    return x_api_key


def rate_limit(identity: str) -> None:
    if RATE_LIMIT_PER_MINUTE <= 0:
        return

    window = int(time.time() // 60)
    current, count = _windows.get(identity, (window, 0))
    if current != window:
        current, count = window, 0

    if count >= RATE_LIMIT_PER_MINUTE:
        _windows[identity] = (current, count)
        raise APIError(
            429,
            "rate_limited",
            f"Limit of {RATE_LIMIT_PER_MINUTE} requests per minute reached.",
            {"retry_after_seconds": 60 - int(time.time() % 60)},
        )

    _windows[identity] = (current, count + 1)


def reset_rate_limits() -> None:
    _windows.clear()


def _meta(request: Request) -> Meta:
    started = getattr(request.state, "started", None)
    return Meta(
        request_id=getattr(request.state, "request_id", "unassigned"),
        timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        duration_ms=round((time.perf_counter() - started) * 1000, 2) if started else 0.0,
        version=VERSION,
    )


def ok(request: Request, data) -> dict:
    return {"success": True, "data": data, "error": None, "meta": _meta(request).model_dump()}


def fail(request: Request, code: str, message: str, details=None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": ErrorBody(code=code, message=message, details=details).model_dump(),
        "meta": _meta(request).model_dump(),
    }