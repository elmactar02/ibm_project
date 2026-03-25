from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.session import get_db, get_engine
from app.db.models import Task
from app.schemas.task import Priority, Status, TaskCreate, TaskRead, TaskUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables at application startup and clean up on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        from app.db.base import Base

        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

# CORS configuration – allow all origins for simplicity.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _task_to_read(task: Task) -> TaskRead:
    """Convert a Task ORM instance to a TaskRead schema.

    Args:
        task: The ORM instance.

    Returns:
        A TaskRead instance populated from the ORM object.
    """
    return TaskRead.model_validate(task, from_attributes=True)


@app.get(
    "/tasks",
    response_model=List[TaskRead],
    summary="List all tasks",
    tags=["tasks"],
)
async def list_tasks(
    status: Optional[Status] = Query(default=None, description="Filter by status"),
    priority: Optional[Priority] = Query(default=None, description="Filter by priority"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, gt=0, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[TaskRead]:
    """Retrieve a list of tasks with optional filters and pagination.

    Args:
        status: Optional status filter.
        priority: Optional priority filter.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Async SQLAlchemy session provided by FastAPI dependency.

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(Task).where(Task.deleted_at.is_(None))

    if status is not None:
        stmt = stmt.where(Task.status == status.value)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority.value)

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [_task_to_read(task) for task in tasks]


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    tags=["tasks"],
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Create a new task record.

    Args:
        payload: Data required to create a task.
        db: Async SQLAlchemy session.

    Returns:
        The created task as a TaskRead schema.

    Raises:
        HTTPException: If the task cannot be created due to integrity errors.
    """
    # Placeholder user_id; in a real app this would come from the auth token.
    user_id = 1

    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status=payload.status.value,
        user_id=user_id,
    )
    db.add(task)
    try:
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create task.",
        ) from exc

    return _task_to_read(task)


@app.get(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Get task details",
    tags=["tasks"],
)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Retrieve a single task by its identifier.

    Args:
        task_id: Identifier of the task.
        db: Async SQLAlchemy session.

    Returns:
        The requested task as a TaskRead schema.

    Raises:
        HTTPException: If the task does not exist.
    """
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _task_to_read(task)


@app.put(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Update an existing task",
    tags=["tasks"],
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Update fields of an existing task.

    Args:
        task_id: Identifier of the task to update.
        payload: Fields to update.
        db: Async SQLAlchemy session.

    Returns:
        The updated task as a TaskRead schema.

    Raises:
        HTTPException: If the task does not exist or update fails due to integrity errors.
    """
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "priority" in update_data and isinstance(update_data["priority"], Priority):
        update_data["priority"] = update_data["priority"].value
    if "status" in update_data and isinstance(update_data["status"], Status):
        update_data["status"] = update_data["status"].value

    for key, value in update_data.items():
        setattr(task, key, value)

    try:
        await db.commit()
        await db.refresh(task)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update task.",
        ) from exc

    return _task_to_read(task)


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    tags=["tasks"],
)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft‑delete a task by setting its ``deleted_at`` timestamp.

    Args:
        task_id: Identifier of the task to delete.
        db: Async SQLAlchemy session.

    Raises:
        HTTPException: If the task does not exist.
    """
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.deleted_at = func.now()
    await db.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)