from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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
        IN_PROGRESS: Task is being worked on.
        DONE: Task is completed.
    """

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task.
        status: Current status of the task.

    Returns:
        TaskCreate: Instance ready for validation and forwarding to the remote API.

    Raises:
        ValueError: If any string field is empty or contains only whitespace.
    """

    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level of the task")
    status: str = Field(..., description="Current status of the task")

    @field_validator("*", mode="before")
    @classmethod
    def _not_empty(cls, v: Optional[str]) -> str:
        """Ensure string fields are not empty or whitespace only.

        Args:
            v: The value to validate.

        Returns:
            The original string if valid.

        Raises:
            ValueError: If the string is empty after stripping.
        """
        if isinstance(v, str) and not v.strip():
            raise ValueError("String fields must not be empty")
        return v


class TaskRead(BaseModel):
    """Schema for reading a task from the remote API.

    Args:
        id: Unique identifier of the task.
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level of the task.
        status: Current status of the task.
        created_at: ISO‑8601 timestamp when the task was created.
        updated_at: ISO‑8601 timestamp when the task was last updated.
        user_id: Identifier of the user who owns the task.

    Returns:
        TaskRead: Instance containing task data returned to the frontend.
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
        priority: New priority level.
        status: New status.

    Returns:
        TaskUpdate: Instance containing the fields to be updated.

    Raises:
        ValueError: If a provided string field is empty after stripping.
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

    @field_validator("*", mode="before")
    @classmethod
    def _strip_empty(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from string fields; keep None as is.

        Args:
            v: The value to process.

        Returns:
            The stripped string or None.

        Raises:
            ValueError: If a provided string is empty after stripping.
        """
        if v is None:
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("String fields must not be empty")
            return stripped
        return v