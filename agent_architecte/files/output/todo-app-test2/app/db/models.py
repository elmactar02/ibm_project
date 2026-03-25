from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class StatusEnum(str, enum.Enum):
    """Enumeration of possible task statuses."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class PriorityEnum(str, enum.Enum):
    """Enumeration of possible task priorities."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class User(Base):
    """SQLAlchemy model representing an application user.

    Attributes
    ----------
    id : int
        Primary key.
    email : str
        Unique e‑mail address of the user.
    hashed_password : str
        Bcrypt‑hashed password.
    created_at : datetime
        Timestamp when the user was created.
    deleted_at : Optional[datetime]
        Soft‑delete timestamp; ``None`` if the user is active.
    tasks : List[Task]
        Collection of tasks owned by the user.
    """

    __tablename__ = "User"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, nullable=False, index=True)
    hashed_password: str = Column(String, nullable=False)
    created_at: datetime = Column(
        DateTime, nullable=False, server_default=func.datetime("now")
    )
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    tasks: List[Task] = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Task(Base):
    """SQLAlchemy model representing a to‑do task.

    Attributes
    ----------
    id : int
        Primary key.
    title : str
        Short title of the task.
    description : Optional[str]
        Detailed description; may be ``None``.
    status : StatusEnum
        Current status of the task.
    priority : PriorityEnum
        Priority level of the task.
    created_at : datetime
        Timestamp when the task was created.
    updated_at : datetime
        Timestamp of the last update.
    user_id : int
        Foreign key referencing the owning ``User``.
    deleted_at : Optional[datetime]
        Soft‑delete timestamp; ``None`` if the task is active.
    owner : User
        The user who owns this task.
    """

    __tablename__ = "Task"

    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String, nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    status: StatusEnum = Column(
        SAEnum(StatusEnum, native_enum=False), nullable=False
    )
    priority: PriorityEnum = Column(
        SAEnum(PriorityEnum, native_enum=False), nullable=False
    )
    created_at: datetime = Column(
        DateTime, nullable=False, server_default=func.datetime("now")
    )
    updated_at: datetime = Column(
        DateTime,
        nullable=False,
        server_default=func.datetime("now"),
        onupdate=func.datetime("now"),
    )
    user_id: int = Column(Integer, ForeignKey("User.id"), nullable=False, index=True)
    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)

    owner: User = relationship("User", back_populates="tasks", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} title={self.title!r} status={self.status.value} "
            f"priority={self.priority.value}>"
        )