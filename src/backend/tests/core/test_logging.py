import io
import json
import logging
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.container import Container
from app.core.logging import JsonFormatter, start_trace
from app.main import create_app
from tests.fakes.health import FakeHealthProbe


def format_record(message: str, context: dict[str, object] | None = None) -> dict[str, object]:
    record = logging.LogRecord("cic.test", logging.INFO, __file__, 1, message, None, None)
    if context is not None:
        record.context = context
    return dict(json.loads(JsonFormatter().format(record)))


def test_log_line_is_json_with_trace_id() -> None:
    trace_id = start_trace()

    entry = format_record("job claimed", {"jobId": "42"})

    assert entry["message"] == "job claimed"
    assert entry["level"] == "INFO"
    assert entry["traceId"] == trace_id
    assert entry["context"] == {"jobId": "42"}


def test_sensitive_context_keys_are_redacted() -> None:
    entry = format_record(
        "login",
        {
            "email": "a@example.com",
            "password": "hunter22",
            "accessToken": "eyJ.abc",
            "Authorization": "Bearer eyJ.abc",
            "api_key": "k",
            "x-api-key": "raw-key",
            "passwordHash": "$argon2id$",
            "headers": {"Cookie": "session=abc", "accept": "json"},
        },
    )

    rendered = json.dumps(entry)
    for secret in ("hunter22", "eyJ.abc", "$argon2id$", "raw-key", "session=abc"):
        assert secret not in rendered
    assert entry["context"] == {
        "email": "a@example.com",
        "password": "***",
        "accessToken": "***",
        "Authorization": "***",
        "api_key": "***",
        "x-api-key": "***",
        "passwordHash": "***",
        "headers": {"Cookie": "***", "accept": "json"},
    }


@pytest.fixture
def request_log_lines() -> Iterator[io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("cic.request")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield stream
    logger.removeHandler(handler)
    logger.setLevel(logging.NOTSET)


def logged_entries(stream: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_request_log_has_trace_id_matching_problem_and_no_credentials(
    app: FastAPI, request_log_lines: io.StringIO
) -> None:
    token = "eyJhbGciOiJIUzI1NiJ9.secret-payload.signature"

    response = TestClient(app).get(
        "/api/v1/missing",
        headers={"Authorization": f"Bearer {token}", "X-API-Key": "raw-key"},
    )

    assert token not in request_log_lines.getvalue()
    assert "raw-key" not in request_log_lines.getvalue()
    [entry] = logged_entries(request_log_lines)
    assert entry["level"] == "INFO"
    assert entry["traceId"] == response.json()["traceId"]
    context = dict(entry["context"])
    assert isinstance(context.pop("durationMs"), float)
    assert context == {"method": "GET", "path": "/api/v1/missing", "status": 404}


@pytest.mark.parametrize(("available", "level"), [(True, "DEBUG"), (False, "INFO")])
def test_health_polls_are_quiet_unless_degraded(
    container: Container, request_log_lines: io.StringIO, available: bool, level: str
) -> None:
    app = create_app(replace(container, health=FakeHealthProbe(available=available)))

    TestClient(app).get("/health")

    [entry] = logged_entries(request_log_lines)
    assert entry["level"] == level
