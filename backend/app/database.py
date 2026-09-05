"""
app/database.py
---------------
Async SQLAlchemy engine, session factory, and FastAPI dependency.
Uses asyncpg as the driver, matching DATABASE_URL from config.
Reference: docs/01-tech-stack.md, docs/02-database-schema.md
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


def _build_engine():
    """
    Create the async engine once, at import time.
    pool_size=5 guards against exceeding Supabase free-tier connection limit (2
    direct; 10 via pooler).  pool_pre_ping ensures stale connections are
    detected and replaced automatically.
    """
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
        # Echo SQL only in development to avoid leaking PII to prod logs.
        echo=settings.is_development,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )


engine = _build_engine()

# Session factory — reused across all requests, never shared between coroutines.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit without re-query
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy models.
    Import this in models.py so Alembic can auto-detect schema changes.
    """
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an AsyncSession for use in FastAPI route handlers.

    Usage:
        @router.get("/something")
        async def handler(db: AsyncSession = Depends(get_db)):
            ...

    The session is always closed (and the transaction rolled back on error)
    even if the route raises an exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
