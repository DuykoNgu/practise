import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.database import create_db_engine, create_session_factory

BACKEND_DIR = Path(__file__).resolve().parents[2]
TEST_DATABASE_URL = os.environ.get("CIC_TEST_DATABASE_URL")


@pytest.fixture
def pg_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    if not TEST_DATABASE_URL:
        pytest.skip("CIC_TEST_DATABASE_URL is not set")
    if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
        pytest.fail("CIC_TEST_DATABASE_URL must point at a database whose name ends with _test")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("DATABASE_SCHEMA", "cic")
    monkeypatch.setenv("JWT_SECRET", "t" * 40)
    return Settings(_env_file=None)


@pytest.fixture
def pg_engine(pg_settings: Settings) -> Iterator[Engine]:
    engine = create_db_engine(pg_settings)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS cic CASCADE"))
    yield engine
    engine.dispose()


@pytest.fixture
def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return config


@pytest.fixture
def migrated(pg_engine: Engine, alembic_config: Config) -> Engine:
    command.upgrade(alembic_config, "head")
    return pg_engine


@pytest.fixture
def session(migrated: Engine) -> Iterator[Session]:
    with create_session_factory(migrated)() as db_session:
        yield db_session
        db_session.rollback()
