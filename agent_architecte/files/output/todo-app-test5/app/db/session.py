from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings

# Default SQLite URL for development; can be overridden via Settings
_DEFAULT_SQLITE_URL: Final[str] = "sqlite+aiosqlite:///./dev.db"


def _build_database_url() -> str:
    """Construct the database URL from settings or fallback.

    Returns:
        str: The SQLAlchemy async database URL.
    """
    settings = Settings()
    # Settings may expose `database_url` or `DATABASE_URL`; try both.
    url: str | None = getattr(settings, "database_url", None) or getattr(
        settings, "DATABASE_URL", None
    )
    return url or _DEFAULT_SQLITE_URL


_engine: AsyncEngine = create_async_engine(
    _build_database_url(),
    echo=False,
    future=True,
)


def get_engine() -> AsyncEngine:
    """Return the global asynchronous SQLAlchemy engine.

    Returns:
        AsyncEngine: The engine used for all async DB operations.
    """
    return _engine


# Session factory bound to the global engine.
AsyncSessionFactory = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a transactional async session.

    Yields:
        AsyncSession: An active asynchronous SQLAlchemy session.

    Raises:
        RuntimeError: If the session cannot be created.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


__all__: list[str] = ["get_engine", "get_db", "AsyncSessionFactory"]