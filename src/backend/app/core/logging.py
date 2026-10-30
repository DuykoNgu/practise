import json
import logging
import sys
import time
from collections.abc import Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

SENSITIVE_KEY_PARTS = ("password", "token", "secret", "authorization", "apikey", "hash", "cookie")
REDACTED = "***"
QUIET_PATHS = frozenset({"/health"})

_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")
_request_logger = logging.getLogger("cic.request")


def start_trace() -> str:
    trace_id = uuid4().hex
    _trace_id.set(trace_id)
    return trace_id


def current_trace_id() -> str:
    return _trace_id.get()


def _is_sensitive(key: str) -> bool:
    normalized = key.lower().replace("_", "").replace("-", "")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _redact_value(key: str, value: object) -> object:
    if _is_sensitive(key):
        return REDACTED
    if isinstance(value, Mapping):
        return redact(value)
    return value


def redact(context: Mapping[str, object]) -> dict[str, object]:
    return {key: _redact_value(key, value) for key, value in context.items()}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "traceId": current_trace_id(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            entry["context"] = redact(context)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)


def _has_json_handler(logger: logging.Logger) -> bool:
    return any(isinstance(handler.formatter, JsonFormatter) for handler in logger.handlers)


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if not _has_json_handler(root):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True


def _is_quiet(path: str, status: int) -> bool:
    return path in QUIET_PATHS and status < 400


class RequestLogMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start_trace()
        started = time.perf_counter()
        status = 500

        async def send_with_status(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_with_status)
        finally:
            _request_logger.log(
                logging.DEBUG if _is_quiet(scope["path"], status) else logging.INFO,
                "request",
                extra={
                    "context": {
                        "method": scope["method"],
                        "path": scope["path"],
                        "status": status,
                        "durationMs": round((time.perf_counter() - started) * 1000, 1),
                    }
                },
            )
