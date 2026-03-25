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

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    """Enum representing task status.

    Attributes:
        TODO: Task is pending.
        IN_PROGRESS: Task is currently being worked on.
        DONE: Task has been completed.
    """

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task (as a string).
        status: Current status of the task (as a string).

    Returns:
        An instance of ``TaskCreate`` ready for validation.

    Raises:
        pydantic.ValidationError: If any field fails validation.
    """

    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level of the task")
    status: str = Field(..., description="Current status of the task")


class TaskRead(BaseModel):
    """Schema for reading task data from the remote API.

    Args:
        id: Unique identifier of the task.
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task (as a string).
        status: Current status of the task (as a string).
        created_at: ISO‑8601 timestamp when the task was created.
        updated_at: ISO‑8601 timestamp when the task was last updated.
        user_id: Identifier of the user who owns the task.

    Returns:
        An instance of ``TaskRead`` containing all readable fields.

    Raises:
        pydantic.ValidationError: If any field fails validation.
    """

    id: int = Field(..., description="Unique identifier of the task")
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level of the task")
    status: str = Field(..., description="Current status of the task")
    created_at: str = Field(..., description="Creation timestamp (ISO‑8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO‑8601)")
    user_id: int = Field(..., description="Owner user identifier")


class TaskUpdate(BaseModel):
    """Schema for partially updating a task.

    All fields are optional; only provided fields will be sent to the remote API.

    Args:
        title: New title for the task.
        description: New description for the task.
        priority: New priority level (as a string).
        status: New status (as a string).

    Returns:
        An instance of ``TaskUpdate`` with the supplied updates.

    Raises:
        pydantic.ValidationError: If any provided field fails validation.
    """

    title: Optional[str] = Field(
        None, description="New title for the task (optional)"
    )
    description: Optional[str] = Field(
        None, description="New description for the task (optional)"
    )
    priority: Optional[str] = Field(
        None, description="New priority level (optional)"
    )
    status: Optional[str] = Field(
        None, description="New status (optional)"
    )