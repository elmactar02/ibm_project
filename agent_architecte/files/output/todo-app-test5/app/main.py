from __future__ import annotations

from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.db.models import Task
from app.db.session import get_db, get_engine
from app.schemas.task import (
    Priority,
    Status,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

def _create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI instance.
    """
    app = FastAPI()

    # CORS configuration – allow all origins for simplicity.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        """Create database tables on application startup."""
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @app.get(
        "/tasks",
        response_model=List[TaskRead],
        summary="List all tasks",
        tags=["tasks"],
    )
    async def list_tasks(
        status: Optional[Status] = Query(default=None, description="Filter by status"),
        priority: Optional[Priority] = Query(default=None, description="Filter by priority"),
        db: AsyncSession = Depends(get_db),
    ) -> List[TaskRead]:
        """Retrieve a list of tasks, optionally filtered by status and priority.

        Args:
            status: Optional status to filter tasks.
            priority: Optional priority to filter tasks.
            db: Async SQLAlchemy session provided by FastAPI dependency.

        Returns:
            List[TaskRead]: List of tasks matching the criteria.

        Raises:
            HTTPException: If a database error occurs.
        """
        stmt = select(Task)
        if status is not None:
            stmt = stmt.where(Task.status == status.value)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority.value)

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
        db: AsyncSession = Depends(get_db),
    ) -> TaskRead:
        """Create a new task record.

        Args:
            payload: Validated task creation data.
            db: Async SQLAlchemy session.

        Returns:
            TaskRead: The newly created task.

        Raises:
            HTTPException: If the task cannot be persisted.
        """
        # Placeholder user_id; replace with actual authenticated user ID.
        user_id = 1

        task = Task(
            title=payload.title,
            description=payload.description,
            priority=payload.priority.value,
            status=payload.status.value,
            user_id=user_id,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return TaskRead.from_orm(task)

    @app.get(
        "/tasks/{task_id}",
        response_model=TaskRead,
        summary="Get task by ID",
        tags=["tasks"],
    )
    async def get_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
    ) -> TaskRead:
        """Retrieve a single task by its identifier.

        Args:
            task_id: Primary key of the task.
            db: Async SQLAlchemy session.

        Returns:
            TaskRead: The requested task.

        Raises:
            HTTPException: 404 if task not found.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found.",
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
        db: AsyncSession = Depends(get_db),
    ) -> TaskRead:
        """Apply partial updates to a task.

        Args:
            task_id: Identifier of the task to update.
            payload: Fields to update.
            db: Async SQLAlchemy session.

        Returns:
            TaskRead: Updated task representation.

        Raises:
            HTTPException: 404 if task does not exist.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found.",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if "priority" in update_data:
            update_data["priority"] = update_data["priority"].value
        if "status" in update_data:
            update_data["status"] = update_data["status"].value

        for key, value in update_data.items():
            setattr(task, key, value)

        await db.commit()
        await db.refresh(task)
        return TaskRead.from_orm(task)

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
        """Remove a task from the database.

        Args:
            task_id: Identifier of the task to delete.
            db: Async SQLAlchemy session.

        Raises:
            HTTPException: 404 if task not found.
        """
        stmt = select(Task).where(Task.id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found.",
            )
        await db.delete(task)
        await db.commit()
        return None

    return app


app: FastAPI = _create_app()