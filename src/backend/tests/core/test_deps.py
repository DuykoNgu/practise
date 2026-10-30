from dataclasses import replace
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.container import Container
from app.core.deps import SessionDep, require_api_client, require_roles
from app.core.security import (
    ApiClient,
    ApiClientKind,
    CurrentUser,
    TokenService,
    UserRole,
    hash_api_key,
)
from app.main import create_app
from tests.fakes.api_clients import FakeApiClientLookup

ITSM_KEY = "itsm-key-0123456789"
ITSM_CLIENT = ApiClient(id=uuid4(), name="ServiceDesk", kind=ApiClientKind.ITSM)


def build_app(container: Container) -> FastAPI:
    app = create_app(container)
    admin_only = require_roles(UserRole.ADMIN, UserRole.IT_MANAGER)
    itsm_client = require_api_client(ApiClientKind.ITSM)
    log_client = require_api_client(ApiClientKind.LOG_SOURCE)

    @app.get("/admin")
    def admin(user: Annotated[CurrentUser, Depends(admin_only)]) -> dict[str, str]:
        return {"role": user.role.value}

    @app.get("/itsm")
    def itsm(client: Annotated[ApiClient, Depends(itsm_client)]) -> dict[str, str]:
        return {"name": client.name}

    @app.get("/logs")
    def logs(client: Annotated[ApiClient, Depends(log_client)]) -> dict[str, str]:
        return {"name": client.name}

    @app.post("/write")
    def write(session: SessionDep, fail: bool = False) -> None:
        session.execute(text("INSERT INTO notes (body) VALUES ('x')"))
        if fail:
            raise RuntimeError("boom")

    return app


@pytest.fixture
def lookup_container(container: Container) -> Container:
    lookup = FakeApiClientLookup({hash_api_key(ITSM_KEY): ITSM_CLIENT})
    return replace(container, api_clients=lambda _: lookup)


@pytest.fixture
def client(lookup_container: Container) -> TestClient:
    return TestClient(build_app(lookup_container), raise_server_exceptions=False)


def bearer(tokens: TokenService, role: UserRole) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens.issue(uuid4(), role).token}"}


def test_missing_token_returns_401(client: TestClient) -> None:
    response = client.get("/admin")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize(
    "header", ["Bearer not-a-token", "Basic dXNlcjpwYXNz", "Bearer", "Token abc"]
)
def test_invalid_authorization_header_returns_401(client: TestClient, header: str) -> None:
    assert client.get("/admin", headers={"Authorization": header}).status_code == 401


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.IT_MANAGER])
def test_allowed_role_passes(client: TestClient, tokens: TokenService, role: UserRole) -> None:
    response = client.get("/admin", headers=bearer(tokens, role))

    assert response.status_code == 200
    assert response.json() == {"role": role.value}


@pytest.mark.parametrize("role", [UserRole.CHANGE_ENGINEER, UserRole.AGENT])
def test_other_role_returns_403(client: TestClient, tokens: TokenService, role: UserRole) -> None:
    response = client.get("/admin", headers=bearer(tokens, role))

    assert response.status_code == 403
    assert response.json()["title"] == "Access denied"


def test_active_api_client_of_matching_kind_is_accepted(client: TestClient) -> None:
    response = client.get("/itsm", headers={"X-API-Key": ITSM_KEY})

    assert response.status_code == 200
    assert response.json() == {"name": "ServiceDesk"}


@pytest.mark.parametrize(
    ("path", "headers"),
    [
        ("/itsm", {}),
        ("/itsm", {"X-API-Key": ""}),
        ("/itsm", {"X-API-Key": "unknown-key"}),
        ("/logs", {"X-API-Key": ITSM_KEY}),
    ],
)
def test_missing_wrong_or_mismatched_api_key_returns_401(
    client: TestClient, path: str, headers: dict[str, str]
) -> None:
    assert client.get(path, headers=headers).status_code == 401


def test_api_key_is_rejected_until_a_lookup_is_bound(container: Container) -> None:
    client = TestClient(build_app(container))

    assert client.get("/itsm", headers={"X-API-Key": ITSM_KEY}).status_code == 401


def count_notes(container: Container) -> int:
    with container.session_factory() as session:
        return int(session.execute(text("SELECT count(*) FROM notes")).scalar_one())


def test_session_commits_on_success_and_rolls_back_on_error(
    lookup_container: Container, client: TestClient
) -> None:
    with lookup_container.engine.begin() as connection:
        connection.execute(text("CREATE TABLE notes (body TEXT)"))

    assert client.post("/write").status_code == 200
    assert client.post("/write", params={"fail": True}).status_code == 500
    assert count_notes(lookup_container) == 1
