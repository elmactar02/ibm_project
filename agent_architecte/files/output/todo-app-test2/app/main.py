from __future__ import annotations

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.session import get_db, get_engine
from app.db.models import Task
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        Configured FastAPI instance with routes and middleware.
    """
    app = FastAPI(title="Task Management API")

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def on_startup() -> None:
        """Initialize database tables on application startup."""
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Task.metadata.create_all)

    @app.get(
        "/tasks",
        response_model=List[TaskRead],
        summary="List all tasks",
        tags=["tasks"],
    )
    async def list_tasks(
        task_status: Optional[Status] = Query(
            default=None, description="Filter by task status"
        ),
        task_priority: Optional[Priority] = Query(
            default=None, description="Filter by task priority"
        ),
        db: AsyncSession = Depends(get_db),
    ) -> List[TaskRead]:
        """Retrieve a list of tasks, optionally filtered by status and priority.

        Args:
            task_status: Optional status to filter tasks.
            task_priority: Optional priority to filter tasks.
            db: Database session provided by FastAPI dependency.

        Returns:
            List of tasks matching the criteria.

        Raises:
            HTTPException: If a database error occurs.
        """
        stmt = select(Task)
        if task_status is not None:
            stmt = stmt.where(Task.status == task_status.value)
        if task_priority is not None:
            stmt = stmt.where(Task.priority == task_priority.value)

        try:
            result = await db.execute(stmt)
            tasks = result.scalars().all()
            return [TaskRead.from_orm(task) for task in tasks]
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

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
            db: Database session provided by FastAPI dependency.

        Returns:
            The created task.

        Raises:
            HTTPException: If the task cannot be persisted.
        """
        new_task = Task(
            title=payload.title,
            description=payload.description,
            priority=payload.priority.value,
            status=payload.status.value,
            user_id=1,  # Placeholder; replace with authenticated user ID.
        )
        db.add(new_task)
        try:
            await db.commit()
            await db.refresh(new_task)
            return TaskRead.from_orm(new_task)
        except SQLAlchemyError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

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
            task_id: Identifier of the task to retrieve.
            db: Database session provided by FastAPI dependency.

        Returns:
            The requested task.

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
        db: AsyncSession = Depends(get_db),
    ) -> TaskRead:
        """Update fields of an existing task.

        Args:
            task_id: Identifier of the task to update.
            payload: Fields to update.
            db: Database session provided by FastAPI dependency.

        Returns:
            The updated task.

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
        if "priority" in update_data and update_data["priority"] is not None:
            update_data["priority"] = update_data["priority"].value
        if "status" in update_data and update_data["status"] is not None:
            update_data["status"] = update_data["status"].value

        for key, value in update_data.items():
            setattr(task, key, value)

        try:
            await db.commit()
            await db.refresh(task)
            return TaskRead.from_orm(task)
        except SQLAlchemyError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

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
        """Delete a task from the database.

        Args:
            task_id: Identifier of the task to delete.
            db: Database session provided by FastAPI dependency.

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
            db.delete(task)
            await db.commit()
        except SQLAlchemyError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

    return app


app: FastAPI = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)