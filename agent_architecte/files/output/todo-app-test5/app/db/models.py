from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Status(str, Enum):
    """Possible states of a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Priority(str, Enum):
    """Possible priority levels of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class User(Base):
    """User of the application."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, nullable=False, index=True)
    hashed_password: str = Column(String, nullable=False)
    created_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    tasks: list[Task] = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Task(Base):
    """Task belonging to a user."""

    __tablename__ = "tasks"

    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String, nullable=False)
    description: str | None = Column(Text, nullable=True)
    status: Status = Column(
        SAEnum(Status, name="status_enum"),
        nullable=False,
        default=Status.TODO,
    )
    priority: Priority = Column(
        SAEnum(Priority, name="priority_enum"),
        nullable=False,
        default=Priority.MEDIUM,
    )
    created_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: datetime = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner: User = relationship("User", back_populates="tasks", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} title={self.title!r} "
            f"status={self.status.value} priority={self.priority.value}>"
        )


__all__: list[str] = ["User", "Task", "Status", "Priority"]