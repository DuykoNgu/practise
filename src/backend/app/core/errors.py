import logging
from collections.abc import Mapping
from http.client import responses as status_phrases
from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import current_trace_id

PROBLEM_MEDIA_TYPE = "application/problem+json"
REQUEST_LOCATIONS = {"body", "query", "path", "header", "cookie"}

_logger = logging.getLogger("cic.errors")


class DomainError(Exception):
    status: ClassVar[int]
    title: ClassVar[str]

    def __init__(
        self, detail: str | None = None, errors: Mapping[str, list[str]] | None = None
    ) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.errors = errors


class InvalidInputError(DomainError):
    status = 400
    title = "Invalid input"


class UnauthorizedError(DomainError):
    status = 401
    title = "Authentication required"


class ForbiddenError(DomainError):
    status = 403
    title = "Access denied"


class NotFoundError(DomainError):
    status = 404
    title = "Not found"


class ConflictError(DomainError):
    status = 409
    title = "Conflict"


def problem(
    status: int,
    title: str,
    detail: str | None = None,
    errors: Mapping[str, list[str]] | None = None,
) -> JSONResponse:
    body: dict[str, object] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "traceId": current_trace_id(),
    }
    if detail:
        body["detail"] = detail
    if errors:
        body["errors"] = dict(errors)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_MEDIA_TYPE)


def field_name(location: tuple[int | str, ...]) -> str:
    parts = [str(part) for part in location]
    if parts and parts[0] in REQUEST_LOCATIONS:
        parts = parts[1:]
    return ".".join(parts) or "request"


def field_errors(exc: RequestValidationError) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        name = "request" if error["type"] == "json_invalid" else field_name(tuple(error["loc"]))
        errors.setdefault(name, []).append(error["msg"])
    return errors


class UnexpectedErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        response_started = False

        async def track_start(message: Message) -> None:
            nonlocal response_started
            response_started = response_started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, receive, track_start)
        except Exception:
            _logger.exception(
                "unhandled error",
                extra={"context": {"method": scope["method"], "path": scope["path"]}},
            )
            if response_started:
                raise
            await problem(500, status_phrases[500])(scope, receive, send)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return problem(exc.status, exc.title, exc.detail, exc.errors)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return problem(InvalidInputError.status, InvalidInputError.title, errors=field_errors(exc))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        response = problem(exc.status_code, status_phrases.get(exc.status_code, "Error"))
        response.headers.update(exc.headers or {})
        return response
