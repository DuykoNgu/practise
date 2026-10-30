from dataclasses import replace
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.container import Container
from app.main import create_app
from tests.fakes.health import FakeHealthProbe


def client_with(container: Container, probe: FakeHealthProbe) -> TestClient:
    return TestClient(create_app(replace(container, health=probe)))


def test_health_is_ok_with_last_job_time(container: Container) -> None:
    finished = datetime(2026, 10, 30, 8, 15, tzinfo=UTC)

    response = client_with(container, FakeHealthProbe(last_job_at=finished)).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "OK",
        "database": "OK",
        "workerLastJobAt": "2026-10-30T08:15:00Z",
    }


def test_health_is_ok_before_any_job_ran(container: Container) -> None:
    response = client_with(container, FakeHealthProbe()).get("/health")

    assert response.status_code == 200
    assert response.json()["workerLastJobAt"] is None


def test_health_returns_503_when_database_is_unavailable(container: Container) -> None:
    response = client_with(container, FakeHealthProbe(available=False)).get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "DEGRADED",
        "database": "UNAVAILABLE",
        "workerLastJobAt": None,
    }


def test_health_is_public_and_outside_api_prefix(container: Container) -> None:
    client = client_with(container, FakeHealthProbe())

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 404
