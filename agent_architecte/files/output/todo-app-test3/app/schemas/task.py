from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    """Enumeration of possible task priorities."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    """Enumeration of possible task statuses."""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Short title of the task.
        description: Optional detailed description.
        priority: Priority level of the task.
        status: Current status of the task.

    Returns:
        An instance of ``TaskCreate`` ready for validation and persistence.
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: Priority = Field(..., description="Priority level of the task")
    status: Status = Field(..., description="Current status of the task")

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    """Schema for reading task data from the API.

    Args:
        id: Primary key identifier.
        title: Short title of the task.
        description: Optional detailed description.
        priority: Priority level of the task.
        status: Current status of the task.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        user_id: Identifier of the owning user.

    Returns:
        An instance of ``TaskRead`` populated from the database model.
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
        description: New description for the task.
        priority: New priority level.
        status: New status.

    Returns:
        An instance of ``TaskUpdate`` containing the fields to modify.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
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