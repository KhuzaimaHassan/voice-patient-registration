"""
alembic/env.py
--------------
Alembic migration environment.

Reads DATABASE_URL from app.config.Settings (via pydantic-settings / .env)
so no secrets are hardcoded in alembic.ini.

Supports both offline (--sql) and online (async) migration modes.
Reference: docs/02-database-schema.md (Alembic Migration Strategy)
"""

import asyncio
from logging.config import fileConfig
import sys
from pathlib import Path

# Add backend directory to sys.path so app package can be imported
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Import app config and models so Alembic can auto-detect schema.
# IMPORTANT: models must be imported BEFORE Base.metadata is used.
# ---------------------------------------------------------------------------
from app.config import get_settings
from app.database import Base
import app.models  # noqa: F401 — ensures Patient model is registered on Base.metadata

# ---------------------------------------------------------------------------
# Alembic Config object (gives access to alembic.ini values)
# ---------------------------------------------------------------------------
config = context.config

# Set up Python logging from alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Override the sqlalchemy.url with the value from our Settings.
# This is the key line — keeps secrets out of alembic.ini.
# ---------------------------------------------------------------------------
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ---------------------------------------------------------------------------
# Target metadata — tells Alembic what the schema SHOULD look like.
# ---------------------------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration (generates SQL without connecting to DB)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL script output instead of connecting to the database.
    Useful for reviewing changes before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render CHECK constraints and other server-side SQL.
        render_as_batch=False,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration (connects to DB and runs migrations)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        # Include schemas (important for Supabase which uses multiple schemas).
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using an async engine.
    Required because our app uses asyncpg (async-only driver).
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Use NullPool for migrations (no persistent connections)
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch to offline or online based on Alembic context
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
