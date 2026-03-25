from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Enum representing task priority levels.

    Attributes:
        HIGH: High priority.
        MEDIUM: Medium priority.
        LOW: Low priority.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Enum representing task workflow status.

    Attributes:
        TODO: Task is pending.
        IN_PROGRESS: Task is being worked on.
        DONE: Task is completed.
    """

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task (optional, defaults to "medium").
        status: Current workflow status of the task (optional, defaults to "todo").

    Returns:
        An instance of TaskCreate.

    Raises:
        pydantic.ValidationError: If validation fails.
    """

    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(default="medium", description="Priority level of the task")
    status: str = Field(default="todo", description="Current workflow status of the task")


class TaskRead(BaseModel):
    """Schema for returning task data to the client.

    Args:
        id: Unique identifier of the task.
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task.
        status: Current workflow status of the task.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        user_id: Identifier of the owning user.

    Returns:
        An instance of TaskRead.

    Raises:
        pydantic.ValidationError: If validation fails.
    """

    id: int = Field(..., description="Unique identifier of the task")
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level of the task")
    status: str = Field(..., description="Current workflow status of the task")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    user_id: int = Field(..., description="Owner user identifier")


class TaskUpdate(BaseModel):
    """Schema for partially updating an existing task.

    Args:
        title: New title for the task.
        description: New description for the task.
        priority: New priority level.
        status: New workflow status.

    Returns:
        An instance of TaskUpdate.

    Raises:
        pydantic.ValidationError: If validation fails.
    """

    title: Optional[str] = Field(None, description="New title for the task")
    description: Optional[str] = Field(None, description="New description for the task")
    priority: Optional[str] = Field(None, description="New priority level")
    status: Optional[str] = Field(None, description="New workflow status")