import logging
from datetime import datetime
from typing import Protocol, cast

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings

CONNECT_TIMEOUT_SECONDS = 5
LAST_JOB_FINISHED_AT = text("SELECT max(finished_at) FROM jobs")

_logger = logging.getLogger("cic.database")


class DatabaseUnavailableError(Exception):
    pass


class HealthProbe(Protocol):
    def last_job_finished_at(self) -> datetime | None: ...


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=CONNECT_TIMEOUT_SECONDS,
        hide_parameters=True,
        connect_args={
            "options": f"-c search_path={settings.database_schema},public -c timezone=UTC",
            "connect_timeout": CONNECT_TIMEOUT_SECONDS,
        },
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


class SqlHealthProbe:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def last_job_finished_at(self) -> datetime | None:
        try:
            with self._engine.connect() as connection:
                return cast(datetime | None, connection.execute(LAST_JOB_FINISHED_AT).scalar_one())
        except SQLAlchemyError as error:
            _logger.warning(
                "database unavailable", extra={"context": {"error": type(error).__name__}}
            )
            raise DatabaseUnavailableError() from error
