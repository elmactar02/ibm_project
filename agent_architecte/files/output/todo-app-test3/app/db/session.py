# app/db/session.py
"""SQLAlchemy async session factory.

Provides the async engine and FastAPI dependency for obtaining an
:class:`sqlalchemy.ext.asyncio.AsyncSession`.

Functions:
    get_engine: Return a singleton async engine configured from Settings.
    get_db: FastAPI dependency yielding an async session.
"""

from collections.abc import AsyncGenerator
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings

# Global engine instance (singleton)
_engine: AsyncEngine | None = None

def get_engine(settings: Settings = Settings()) -> AsyncEngine:
    """Create or retrieve the global async SQLAlchemy engine.

    Args:
        settings: Application settings containing the database URL.

    Returns:
        An :class:`sqlalchemy.ext.asyncio.AsyncEngine` instance.

    Raises:
        ValueError: If ``settings.DATABASE_URL`` is empty.
    """
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in Settings.")
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.SQLALCHEMY_ECHO,
            future=True,
        )
    return _engine


# Session factory bound to the singleton engine.
_SessionFactory: Final = async_sessionmaker(
    bind=get_engine(),
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Yields:
        An instance of :class:`sqlalchemy.ext.asyncio.AsyncSession`.

    Raises:
        RuntimeError: If the session cannot be created.
    """
    session: AsyncSession = _SessionFactory()
    try:
        yield session
    finally:
        await session.close()


__all__: list[str] = ["get_engine", "get_db"]