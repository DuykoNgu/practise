import logging
from dataclasses import replace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.container import Container
from app.core.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidInputError,
    NotFoundError,
    UnauthorizedError,
)
from app.main import create_app

SECRET_DETAIL = "password=hunter2 at /srv/app/core/secret.py"


class Payload(BaseModel):
    name: str = Field(min_length=3)
    size: int


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    errors: dict[str, DomainError] = {
        "invalid": InvalidInputError(errors={"email": ["Email is already used"]}),
        "unauthorized": UnauthorizedError(),
        "forbidden": ForbiddenError(),
        "not-found": NotFoundError("Change not found"),
        "conflict": ConflictError("Email is already used"),
    }

    @app.get("/raise/{kind}")
    def raise_error(kind: str) -> None:
        if kind == "unexpected":
            raise RuntimeError(SECRET_DETAIL)
        if kind == "unregistered-status":
            raise HTTPException(status_code=499)
        raise errors[kind]

    @app.post("/payload")
    def accept(payload: Payload) -> Payload:
        return payload

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("kind", "status", "title"),
    [
        ("invalid", 400, "Invalid input"),
        ("unauthorized", 401, "Authentication required"),
        ("forbidden", 403, "Access denied"),
        ("not-found", 404, "Not found"),
        ("conflict", 409, "Conflict"),
    ],
)
def test_domain_errors_become_problem_json(
    client: TestClient, kind: str, status: int, title: str
) -> None:
    response = client.get(f"/raise/{kind}")

    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == status
    assert body["title"] == title
    assert len(body["traceId"]) == 32


def test_domain_error_keeps_detail_and_field_errors(client: TestClient) -> None:
    assert client.get("/raise/not-found").json()["detail"] == "Change not found"
    assert client.get("/raise/invalid").json()["errors"] == {"email": ["Email is already used"]}


def test_request_validation_returns_400_with_errors_per_field(client: TestClient) -> None:
    response = client.post("/payload", json={"name": "zq", "size": "large"})

    assert response.status_code == 400
    body = response.json()
    assert body["title"] == "Invalid input"
    assert set(body["errors"]) == {"name", "size"}
    assert "zq" not in response.text


def test_unknown_route_returns_problem_json(client: TestClient) -> None:
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Not Found"


def test_unexpected_error_returns_500_with_trace_id_only(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="cic.errors"):
        response = client.get("/raise/unexpected")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"type", "title", "status", "traceId"}
    assert SECRET_DETAIL not in response.text
    assert "Traceback" not in response.text
    assert any(record.levelno == logging.ERROR for record in caplog.records)


def test_malformed_json_is_a_request_level_error(client: TestClient) -> None:
    response = client.post(
        "/payload", content=b'{"name": ', headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert list(response.json()["errors"]) == ["request"]


def test_unregistered_http_status_keeps_its_code(client: TestClient) -> None:
    response = client.get("/raise/unregistered-status")

    assert response.status_code == 499
    assert response.json()["title"] == "Error"


def test_unexpected_error_is_logged_once_and_keeps_cors_headers(
    container: Container, caplog: pytest.LogCaptureFixture
) -> None:
    settings = container.settings.model_copy(update={"cors_origins": ["http://localhost:3000"]})
    app = create_app(replace(container, settings=settings))

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError(SECRET_DETAIL)

    with caplog.at_level(logging.ERROR):
        response = TestClient(app, raise_server_exceptions=False).get(
            "/boom", headers={"Origin": "http://localhost:3000"}
        )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert len([r for r in caplog.records if r.levelno == logging.ERROR]) == 1
