from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import Settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import (
    CurrentUser,
    PasswordHasher,
    TokenService,
    UserRole,
    hash_api_key,
)
from tests.conftest import TEST_JWT_SECRET


@pytest.fixture
def service_at(settings: Settings) -> Callable[[datetime], TokenService]:
    def build(moment: datetime) -> TokenService:
        return TokenService.from_settings(settings, clock=lambda: moment)

    return build


def test_issued_token_decodes_to_current_user(tokens: TokenService) -> None:
    user_id = uuid4()

    token = tokens.issue(user_id, UserRole.IT_MANAGER)

    assert tokens.decode(token.token) == CurrentUser(id=user_id, role=UserRole.IT_MANAGER)


def test_token_expires_thirty_minutes_after_issue(
    service_at: Callable[[datetime], TokenService],
) -> None:
    issued_at = datetime.now(UTC).replace(microsecond=0)

    token = service_at(issued_at).issue(uuid4(), UserRole.AGENT)

    claims = jwt.decode(token.token, TEST_JWT_SECRET, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 30 * 60
    assert token.expires_at == issued_at + timedelta(minutes=30)


def test_expired_token_is_rejected(
    tokens: TokenService, service_at: Callable[[datetime], TokenService]
) -> None:
    issued_long_ago = datetime.now(UTC) - timedelta(minutes=31)
    token = service_at(issued_long_ago).issue(uuid4(), UserRole.ADMIN)

    with pytest.raises(UnauthorizedError):
        tokens.decode(token.token)


def test_token_signed_with_another_secret_is_rejected(tokens: TokenService) -> None:
    forged = TokenService("another-secret-that-is-long-enough!!", "HS256", 30)
    token = forged.issue(uuid4(), UserRole.ADMIN)

    with pytest.raises(UnauthorizedError):
        tokens.decode(token.token)


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "not-a-uuid", "role": "ADMIN"},
        {"sub": str(uuid4()), "role": "SUPERUSER"},
        {"sub": str(uuid4())},
    ],
)
def test_token_with_invalid_claims_is_rejected(
    tokens: TokenService, claims: dict[str, str]
) -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {**claims, "iat": now, "exp": now + timedelta(minutes=5)}, TEST_JWT_SECRET, "HS256"
    )

    with pytest.raises(UnauthorizedError):
        tokens.decode(token)


def test_garbage_token_is_rejected(tokens: TokenService) -> None:
    with pytest.raises(UnauthorizedError):
        tokens.decode("not.a.jwt")


def test_current_user_require_checks_role() -> None:
    agent = CurrentUser(id=uuid4(), role=UserRole.AGENT)

    agent.require([UserRole.AGENT, UserRole.ADMIN])
    with pytest.raises(ForbiddenError):
        agent.require([UserRole.ADMIN])


def test_password_hash_is_salted_argon2_and_verifies() -> None:
    hasher = PasswordHasher()

    first = hasher.hash("correct horse")
    second = hasher.hash("correct horse")

    assert first.startswith("$argon2id$")
    assert first != second
    assert "correct horse" not in first
    assert hasher.verify("correct horse", first)
    assert not hasher.verify("wrong horse", first)


def test_api_key_hash_is_deterministic_and_hides_the_key() -> None:
    key = "itsm-key-0123456789"

    assert hash_api_key(key) == hash_api_key(key)
    assert hash_api_key(key) != hash_api_key("itsm-key-0123456788")
    assert key not in hash_api_key(key)
    assert len(hash_api_key(key)) == 64
