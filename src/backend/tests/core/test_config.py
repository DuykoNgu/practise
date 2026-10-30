import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture(autouse=True)
def base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://cic:pw@db:5432/cic")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://cic.example.com")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:3000", "https://cic.example.com"]
    assert settings.database_schema == "cic"
    assert settings.jwt_expire_minutes == 30
    assert "pw" not in repr(settings)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("DATABASE_SCHEMA", "cic; DROP SCHEMA public"),
        ("JWT_SECRET", "short"),
        ("JWT_ALGORITHM", "none"),
        ("JWT_SECRET", "change-me-to-a-long-random-string"),
        ("JWT_ALGORITHM", "HS512"),
    ],
)
def test_unsafe_settings_are_rejected(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    for secret in ("x" * 40, "change-me-to", "pw@db"):
        assert secret not in str(error.value)
