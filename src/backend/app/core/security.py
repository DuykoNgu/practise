import hashlib
from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import Settings
from app.core.errors import ForbiddenError, UnauthorizedError

REQUIRED_CLAIMS = ["exp", "iat", "sub", "role"]


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    IT_MANAGER = "IT_MANAGER"
    CHANGE_ENGINEER = "CHANGE_ENGINEER"
    AGENT = "AGENT"


class ApiClientKind(StrEnum):
    ITSM = "ITSM"
    LOG_SOURCE = "LOG_SOURCE"


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    role: UserRole

    def require(self, roles: Collection[UserRole]) -> None:
        if self.role not in roles:
            raise ForbiddenError()


@dataclass(frozen=True)
class ApiClient:
    id: UUID
    name: str
    kind: ApiClientKind


class ApiClientLookup(Protocol):
    def find_active(self, key_hash: str, kind: ApiClientKind) -> ApiClient | None: ...


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_at: datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


class TokenService:
    def __init__(
        self,
        secret: str,
        algorithm: str,
        expire_minutes: int,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._lifetime = timedelta(minutes=expire_minutes)
        self._clock = clock

    @classmethod
    def from_settings(
        cls, settings: Settings, clock: Callable[[], datetime] = utc_now
    ) -> "TokenService":
        return cls(
            secret=settings.jwt_secret.get_secret_value(),
            algorithm=settings.jwt_algorithm,
            expire_minutes=settings.jwt_expire_minutes,
            clock=clock,
        )

    def issue(self, user_id: UUID, role: UserRole) -> AccessToken:
        issued_at = self._clock()
        expires_at = issued_at + self._lifetime
        claims = {"sub": str(user_id), "role": role.value, "iat": issued_at, "exp": expires_at}
        return AccessToken(jwt.encode(claims, self._secret, self._algorithm), expires_at)

    def decode(self, token: str) -> CurrentUser:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": REQUIRED_CLAIMS},
            )
            return CurrentUser(id=UUID(claims["sub"]), role=UserRole(claims["role"]))
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise UnauthorizedError() from error


class PasswordHasher:
    def __init__(self) -> None:
        self._hash = PasswordHash((Argon2Hasher(),))

    def hash(self, plain: str) -> str:
        return self._hash.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return self._hash.verify(plain, hashed)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
