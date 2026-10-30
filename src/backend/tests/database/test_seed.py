import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy import table as sa_table
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import ApiClientKind, PasswordHasher, hash_api_key
from app.seed import (
    CATEGORIES,
    DEPARTMENTS,
    SeedError,
    create_api_client,
    main,
    rotate_api_client,
    seed_administrator,
    seed_reference_data,
)

PASSWORD = "a-long-admin-password"


def count(session: Session, table: str) -> int:
    return session.execute(select(func.count()).select_from(sa_table(table))).scalar_one()


def test_reference_data_is_seeded_once(session: Session) -> None:
    seed_reference_data(session)
    seed_reference_data(session)

    assert count(session, "departments") == len(DEPARTMENTS)
    assert count(session, "categories") == len(CATEGORIES)
    assert count(session, "settings") == 1
    assert count(session, "device_groups") > 0


def test_device_groups_map_to_department_and_branch(session: Session) -> None:
    seed_reference_data(session)

    unmapped = session.execute(
        text("SELECT count(*) FROM device_groups WHERE department_id IS NULL OR branch_id IS NULL")
    ).scalar_one()
    assert unmapped == 0


def test_categories_carry_keywords(session: Session) -> None:
    seed_reference_data(session)

    keywords = session.execute(
        text("SELECT keywords FROM categories WHERE name = 'VPN'")
    ).scalar_one()
    assert "vpn" in keywords


def test_administrator_is_created_once_with_hashed_password(session: Session) -> None:
    assert seed_administrator(session, "Admin@Example.com", "Admin", PASSWORD) is True
    assert seed_administrator(session, "admin@example.com", "Admin", PASSWORD) is False

    role, password_hash = session.execute(
        text("SELECT role, password_hash FROM app_users WHERE email = 'admin@example.com'")
    ).one()
    assert count(session, "app_users") == 1
    assert role == "ADMIN"
    assert PasswordHasher().verify(PASSWORD, password_hash)


def test_short_administrator_password_is_rejected(session: Session) -> None:
    with pytest.raises(SeedError):
        seed_administrator(session, "admin@example.com", "Admin", "short")

    assert count(session, "app_users") == 0


def test_api_client_stores_only_the_key_hash(session: Session) -> None:
    api_key = create_api_client(session, "itsm-main", ApiClientKind.ITSM)

    kind, key_hash = session.execute(text("SELECT kind, key_hash FROM api_clients")).one()
    assert kind == "ITSM"
    assert key_hash == hash_api_key(api_key)
    assert api_key not in key_hash


def test_duplicate_api_client_name_is_rejected(session: Session) -> None:
    create_api_client(session, "itsm-main", ApiClientKind.ITSM)

    with pytest.raises(SeedError):
        create_api_client(session, "itsm-main", ApiClientKind.LOG_SOURCE)


def test_rotation_replaces_the_key_and_keeps_a_revoked_client_revoked(session: Session) -> None:
    old_key = create_api_client(session, "logs-main", ApiClientKind.LOG_SOURCE)
    session.execute(text("UPDATE api_clients SET is_active = false"))

    new_key = rotate_api_client(session, "logs-main")

    key_hash, is_active = session.execute(text("SELECT key_hash, is_active FROM api_clients")).one()
    assert new_key != old_key
    assert key_hash == hash_api_key(new_key)
    assert is_active is False


def test_rotating_an_unknown_client_fails(session: Session) -> None:
    with pytest.raises(SeedError):
        rotate_api_client(session, "missing")


def test_cli_seed_runs_twice_without_error(
    migrated: Engine, pg_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.seed.getpass.getpass", lambda _prompt: PASSWORD)
    monkeypatch.setattr("app.seed.Settings", lambda: pg_settings)
    argv = ["seed", "--admin-email", "admin@example.com"]

    assert main(argv) == 0
    assert main(argv) == 0

    with migrated.connect() as connection:
        users = connection.execute(text("SELECT count(*) FROM app_users")).scalar_one()
    assert users == 1


def test_cli_reports_a_rejected_request_with_exit_code_1(
    migrated: Engine, pg_settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("app.seed.Settings", lambda: pg_settings)
        assert main(["rotate-api-client", "--name", "missing"]) == 1

    assert "does not exist" in capsys.readouterr().err


def test_cli_rejects_mismatched_passwords(
    migrated: Engine,
    pg_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = iter([PASSWORD, "another-password-1"])
    monkeypatch.setattr("app.seed.getpass.getpass", lambda _prompt: next(answers))
    monkeypatch.setattr("app.seed.Settings", lambda: pg_settings)

    assert main(["seed", "--admin-email", "admin@example.com"]) == 1
    assert "do not match" in capsys.readouterr().err
