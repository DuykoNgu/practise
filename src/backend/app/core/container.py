from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.database import (
    HealthProbe,
    SqlHealthProbe,
    create_db_engine,
    create_session_factory,
)
from app.core.security import ApiClientLookup, PasswordHasher, TokenService


@dataclass(frozen=True)
class Container:
    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    tokens: TokenService
    passwords: PasswordHasher
    health: HealthProbe
    api_clients: Callable[[Session], ApiClientLookup] | None = None


def build_container(settings: Settings) -> Container:
    engine = create_db_engine(settings)
    return Container(
        settings=settings,
        engine=engine,
        session_factory=create_session_factory(engine),
        tokens=TokenService.from_settings(settings),
        passwords=PasswordHasher(),
        health=SqlHealthProbe(engine),
    )
