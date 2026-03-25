from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Priority(str, Enum):
    """Priority levels for a task."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Possible states of a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Title of the task.
        description: Optional detailed description.
        priority: Priority level; defaults to ``Priority.MEDIUM``.
        status: Initial status; defaults to ``Status.TODO``.

    Returns:
        An instance of ``TaskCreate`` ready for validation and persistence.

    Raises:
        pydantic.ValidationError: If any field fails validation.
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Longer free‑form text."
    )
    priority: Priority = Field(default=Priority.MEDIUM)
    status: Status = Field(default=Status.TODO)

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    """Schema for reading task data from the API.

    Args:
        id: Primary key of the task.
        title: Title of the task.
        description: Optional description.
        priority: Priority level.
        status: Current status.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        user_id: Identifier of the owning user.

    Returns:
        An immutable representation of a task suitable for response payloads.

    Raises:
        pydantic.ValidationError: If any field fails validation.
    """

    id: int
    title: str
    description: Optional[str] = None
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Schema for partially updating a task.

    All fields are optional; only provided values will be applied.

    Args:
        title: New title for the task.
        description: New description.
        priority: Updated priority level.
        status: Updated status.

    Returns:
        An instance of ``TaskUpdate`` containing the changes.

    Raises:
        pydantic.ValidationError: If any field fails validation.
    """

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="New title."
    )
    description: Optional[str] = Field(
        default=None, max_length=2000, description="New description."
    )
    priority: Optional[Priority] = None
    status: Optional[Status] = None

    model_config = ConfigDict(from_attributes=True)


__all__: list[str] = [
    "Priority",
    "Status",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
]