from sqlalchemy import text

from alembic import context
from app.core.config import Settings
from app.core.database import create_db_engine

MIGRATED_SCHEMA = "cic"

settings = Settings()
if settings.database_schema != MIGRATED_SCHEMA:
    raise RuntimeError(f"DATABASE_SCHEMA must be '{MIGRATED_SCHEMA}': cic.sql creates that schema")

engine = create_db_engine(settings)

with engine.connect() as connection:
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.database_schema}"))
    connection.commit()
    context.configure(
        connection=connection,
        target_metadata=None,
        version_table_schema=settings.database_schema,
    )
    with context.begin_transaction():
        context.run_migrations()

engine.dispose()
