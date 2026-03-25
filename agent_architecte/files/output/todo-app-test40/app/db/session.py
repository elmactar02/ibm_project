from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings

__all__: list[str] = ["get_engine", "get_db"]


_engine: Optional[AsyncEngine] = None
_SessionFactory: Optional[async_sessionmaker[AsyncSession]] = None


def _build_engine(database_url: str) -> AsyncEngine:
    """Create an AsyncEngine for the given database URL.

    Args:
        database_url: The database connection string compatible with SQLAlchemy
            async drivers (e.g. ``postgresql+asyncpg://...`` or
            ``sqlite+aiosqlite:///./test.db``).

    Returns:
        An initialized :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.

    Raises:
        ValueError: If ``database_url`` is empty or None.
    """
    if not database_url:
        raise ValueError("DATABASE_URL must be a non‑empty string.")
    return create_async_engine(database_url, future=True, echo=False)


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return a singleton AsyncEngine instance.

    The engine is created on first call using the provided ``Settings`` or,
    if omitted, a new ``Settings`` instance.

    Args:
        settings: Optional ``Settings`` object containing ``DATABASE_URL``.
            If ``None``, a fresh ``Settings`` instance is instantiated.

    Returns:
        The global :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.

    Raises:
        RuntimeError: If engine creation fails due to an invalid URL.
    """
    global _engine
    if _engine is None:
        cfg = settings or Settings()
        try:
            _engine = _build_engine(cfg.DATABASE_URL)
        except Exception as exc:
            raise RuntimeError("Failed to create async engine.") from exc
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create (or retrieve) the async session factory bound to the engine.

    Returns:
        An :class:`~sqlalchemy.ext.asyncio.async_sessionmaker` configured with
        ``expire_on_commit=False`` for typical FastAPI usage.
    """
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _SessionFactory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an :class:`AsyncSession`.

    The session is automatically closed after the request finishes.

    Yields:
        An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.

    Raises:
        RuntimeError: If the session cannot be instantiated.
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()