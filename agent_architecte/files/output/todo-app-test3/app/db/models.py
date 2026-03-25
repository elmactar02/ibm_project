from __future__ import annotations

import enum
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Status(str, enum.Enum):
    """Enumeration of possible task statuses."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Priority(str, enum.Enum):
    """Enumeration of possible task priorities."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class User(Base):
    """SQLAlchemy model representing an application user.

    Attributes:
        id: Primary key identifier.
        email: Unique email address of the user.
        hashed_password: Password hash stored for authentication.
        created_at: Timestamp of user creation.
        tasks: Collection of tasks owned by the user.
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tasks: Mapped[List[Task]] = relationship(
        "Task", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Task(Base):
    """SQLAlchemy model representing a to‑do task.

    Attributes:
        id: Primary key identifier.
        title: Short title of the task.
        description: Optional detailed description.
        status: Current status of the task.
        priority: Priority level of the task.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        user_id: Foreign key referencing the owning user.
        user: Relationship to the owning ``User`` instance.
    """

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status.value}>"


__all__: list[str] = ["User", "Task", "Status", "Priority"]