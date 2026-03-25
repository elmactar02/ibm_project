from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Enumeration of task priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Enumeration of task status values."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: The title of the task.
        description: Optional detailed description of the task.
        priority: Priority level of the task.
        status: Current status of the task.

    Returns:
        A validated TaskCreate instance.
    """

    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: Priority
    status: Status


class TaskRead(BaseModel):
    """Schema for reading task data.

    Args:
        id: Unique identifier of the task.
        title: The title of the task.
        description: Optional detailed description of the task.
        priority: Priority level of the task.
        status: Current status of the task.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp when the task was last updated.
        user_id: Identifier of the user who owns the task.

    Returns:
        A validated TaskRead instance.
    """

    id: UUID
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    created_at: datetime
    updated_at: datetime
    user_id: UUID


class TaskUpdate(BaseModel):
    """Schema for updating an existing task.

    Args:
        title: Optional new title for the task.
        description: Optional new description for the task.
        priority: Optional new priority level.
        status: Optional new status value.

    Returns:
        A validated TaskUpdate instance.
    """

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    priority: Optional[Priority] = None
    status: Optional[Status] = None
