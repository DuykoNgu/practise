from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.container import Container
from app.core.database import create_session_factory
from app.core.security import PasswordHasher, TokenService
from app.main import create_app
from tests.fakes.health import FakeHealthProbe

TEST_JWT_SECRET = "test-secret-that-is-long-enough-for-hs256"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        database_url=SecretStr("sqlite://"),
        jwt_secret=SecretStr(TEST_JWT_SECRET),
    )


@pytest.fixture
def tokens(settings: Settings) -> TokenService:
    return TokenService.from_settings(settings)


@pytest.fixture
def container(settings: Settings, tokens: TokenService) -> Iterator[Container]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    yield Container(
        settings=settings,
        engine=engine,
        session_factory=create_session_factory(engine),
        tokens=tokens,
        passwords=PasswordHasher(),
        health=FakeHealthProbe(),
    )
    engine.dispose()


@pytest.fixture
def app(container: Container) -> FastAPI:
    return create_app(container)
