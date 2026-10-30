import pytest
from alembic.config import Config
from sqlalchemy import Engine, inspect, text

from alembic import command

EXPECTED_TABLES = {
    "app_users",
    "api_clients",
    "departments",
    "branches",
    "software",
    "device_groups",
    "categories",
    "changes",
    "tickets",
    "error_logs",
    "baseline_runs",
    "anomalies",
    "suspects",
    "suggestions",
    "jobs",
    "settings",
    "audit_logs",
}


def test_upgrade_creates_schema_with_default_settings(migrated: Engine) -> None:
    tables = set(inspect(migrated).get_table_names(schema="cic"))
    with migrated.connect() as connection:
        threshold = connection.execute(text("SELECT anomaly_threshold FROM settings")).scalar_one()

    assert tables >= EXPECTED_TABLES
    assert float(threshold) == 3.0


def test_upgrade_twice_is_a_no_op(migrated: Engine, alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")

    assert "tickets" in inspect(migrated).get_table_names(schema="cic")


def test_initial_schema_cannot_be_downgraded(migrated: Engine, alembic_config: Config) -> None:
    with pytest.raises(NotImplementedError):
        command.downgrade(alembic_config, "base")

    assert "tickets" in inspect(migrated).get_table_names(schema="cic")


def test_upgrade_refuses_another_schema_name(
    pg_engine: Engine, alembic_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_SCHEMA", "cic_staging")

    with pytest.raises(RuntimeError, match="DATABASE_SCHEMA"):
        command.upgrade(alembic_config, "head")
