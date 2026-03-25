from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Priority(str, Enum):
    """Enumeration of task priority levels.

    Attributes:
        HIGH: Highest priority.
        MEDIUM: Default priority.
        LOW: Lowest priority.
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    """Enumeration of task status values.

    Attributes:
        TODO: Task has not been started.
        IN_PROGRESS: Task is currently being worked on.
        DONE: Task has been completed.
    """

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Short title of the task.
        description: Optional detailed description.
        priority: Desired priority level.
        status: Initial status of the task.
    """

    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    """Schema for reading task details.

    Args:
        id: Unique identifier of the task.
        title: Short title of the task.
        description: Optional detailed description.
        priority: Priority level of the task.
        status: Current status of the task.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        user_id: Identifier of the owning user.
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
    """Schema for updating an existing task.

    Args:
        title: New title for the task.
        description: New description for the task.
        priority: Updated priority level.
        status: Updated status.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None

    model_config = ConfigDict(from_attributes=True)


__all__: list[str] = ["Priority", "Status", "TaskCreate", "TaskRead", "TaskUpdate"]