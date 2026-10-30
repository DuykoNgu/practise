from collections.abc import Sequence
from pathlib import Path

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA_SQL = Path(__file__).resolve().parents[4] / "src" / "database" / "cic.sql"


def upgrade() -> None:
    op.get_bind().exec_driver_sql(SCHEMA_SQL.read_text(encoding="utf-8"))


def downgrade() -> None:
    raise NotImplementedError("The initial schema cannot be downgraded")
