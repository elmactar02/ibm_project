from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def _create_engine() -> AsyncEngine:
    """Create a SQLAlchemy async engine based on application settings.

    Returns
    -------
    AsyncEngine
        An asynchronous SQLAlchemy engine bound to the configured database URL.

    Raises
    ------
    ValueError
        If the ``DATABASE_URL`` setting is empty or malformed.
    """
    settings = Settings()
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL must be provided in Settings.")
    return create_async_engine(
        settings.DATABASE_URL,
        future=True,
        echo=False,
    )


_engine: AsyncEngine = _create_engine()
_async_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


def get_engine() -> AsyncEngine:
    """Return the singleton async engine used throughout the application.

    Returns
    -------
    AsyncEngine
        The pre‑created asynchronous engine instance.
    """
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session.

    Yields
    ------
    AsyncSession
        An active asynchronous SQLAlchemy session.

    Raises
    ------
    RuntimeError
        If the session cannot be created.
    """
    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()