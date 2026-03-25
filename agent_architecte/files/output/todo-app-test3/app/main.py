from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Select, delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.session import get_db, get_engine
from app.db.models import Task
from app.db.base import Base
from app.schemas.task import (
    Priority,
    Status,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup and close the engine on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None.

    Raises:
        RuntimeError: If table creation fails.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except SQLAlchemyError as exc:
            raise RuntimeError("Failed to create database tables") from exc
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _apply_filters(
    stmt: Select[Task],
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
) -> Select[Task]:
    """Apply optional status and priority filters to a SQLAlchemy statement.

    Args:
        stmt: The initial SQLAlchemy selectable.
        status: Optional status to filter by.
        priority: Optional priority to filter by.

    Returns:
        The statement with applied filters.
    """
    if status is not None:
        stmt = stmt.where(Task.status == status.value)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority.value)
    return stmt


@app.get(
    "/tasks",
    response_model=List[TaskRead],
    summary="List all tasks",
    tags=["tasks"],
)
async def list_tasks(
    status: Optional[Status] = Query(
        None, description="Filter tasks by status"
    ),
    priority: Optional[Priority] = Query(
        None, description="Filter tasks by priority"
    ),
    db: AsyncGenerator[AsyncSession, None] = Depends(get_db),
) -> List[TaskRead]:
    """Retrieve a list of tasks, optionally filtered by status and priority.

    Args:
        status: Optional status filter.
        priority: Optional priority filter.
        db: Async database session provided by FastAPI dependency.

    Returns:
        A list of ``TaskRead`` objects.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(Task)
    stmt = _apply_filters(stmt, status=status, priority=priority)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [TaskRead.from_orm(task) for task in tasks]


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    tags=["tasks"],
)
async def create_task(
    payload: TaskCreate,
    db: AsyncGenerator[AsyncSession, None] = Depends(get_db),
) -> TaskRead:
    """Create a new task record.

    Args:
        payload: Validated task creation data.
        db: Async database session provided by FastAPI dependency.

    Returns:
        The created task as ``TaskRead``.

    Raises:
        HTTPException: If the task cannot be persisted.
    """
    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status=payload.status.value,
        user_id=1,  # Placeholder; replace with authenticated user ID.
    )
    db.add(task)
    try:
        await db.commit()
        await db.refresh(task)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        ) from exc
    return TaskRead.from_orm(task)


@app.get(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Get task details",
    tags=["tasks"],
)
async def get_task(
    task_id: int,
    db: AsyncGenerator[AsyncSession, None] = Depends(get_db),
) -> TaskRead:
    """Retrieve a single task by its identifier.

    Args:
        task_id: Identifier of the task to retrieve.
        db: Async database session provided by FastAPI dependency.

    Returns:
        The requested task as ``TaskRead``.

    Raises:
        HTTPException: If the task does not exist.
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return TaskRead.from_orm(task)


@app.put(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Update an existing task",
    tags=["tasks"],
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncGenerator[AsyncSession, None] = Depends(get_db),
) -> TaskRead:
    """Apply partial updates to an existing task.

    Args:
        task_id: Identifier of the task to update.
        payload: Fields to update.
        db: Async database session provided by FastAPI dependency.

    Returns:
        The updated task as ``TaskRead``.

    Raises:
        HTTPException: If the task does not exist or update fails.
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "priority" in update_data:
        update_data["priority"] = update_data["priority"].value
    if "status" in update_data:
        update_data["status"] = update_data["status"].value

    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        await db.commit()
        await db.refresh(task)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task",
        ) from exc
    return TaskRead.from_orm(task)


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    tags=["tasks"],
)
async def delete_task(
    task_id: int,
    db: AsyncGenerator[AsyncSession, None] = Depends(get_db),
) -> None:
    """Delete a task permanently.

    Args:
        task_id: Identifier of the task to delete.
        db: Async database session provided by FastAPI dependency.

    Raises:
        HTTPException: If the task does not exist or deletion fails.
    """
    stmt = select(Task).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    try:
        await db.delete(task)
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        ) from exc
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)