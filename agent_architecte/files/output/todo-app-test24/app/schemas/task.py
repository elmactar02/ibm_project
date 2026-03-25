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
    """Enum representing task workflow status.

    Attributes:
        TODO: Task not started.
        IN_PROGRESS: Task is being worked on.
        DONE: Task completed.
    """
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task.

    Args:
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level; must be one of ``Priority`` values.
        status: Current status; must be one of ``Status`` values.

    Returns:
        An instance of ``TaskCreate`` validated against the provided data.

    Raises:
        ValueError: If ``priority`` or ``status`` contain invalid values.
    """

    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level (HIGH, MEDIUM, LOW)")
    status: str = Field(..., description="Task status (TODO, IN_PROGRESS, DONE)")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate that ``priority`` matches a defined ``Priority`` enum value.

        Args:
            v: The priority string to validate.

        Returns:
            The original priority string if valid.

        Raises:
            ValueError: If ``v`` is not a valid ``Priority``.
        """
        if v not in Priority.__members__:
            raise ValueError(f"Invalid priority '{v}'. Expected one of: {', '.join(Priority.__members__)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate that ``status`` matches a defined ``Status`` enum value.

        Args:
            v: The status string to validate.

        Returns:
            The original status string if valid.

        Raises:
            ValueError: If ``v`` is not a valid ``Status``.
        """
        if v not in Status.__members__:
            raise ValueError(f"Invalid status '{v}'. Expected one of: {', '.join(Status.__members__)}")
        return v


class TaskRead(BaseModel):
    """Schema for returning task data to the client.

    Args:
        id: Integer identifier of the task.
        title: Title of the task.
        description: Detailed description of the task.
        priority: Priority level (HIGH, MEDIUM, LOW).
        status: Current status (TODO, IN_PROGRESS, DONE).
        created_at: ISO‑8601 timestamp of creation.
        updated_at: ISO‑8601 timestamp of last update.
        user_id: Identifier of the owning user.

    Returns:
        An instance of ``TaskRead`` containing validated task information.
    """

    id: int = Field(..., description="Task identifier")
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Detailed description of the task")
    priority: str = Field(..., description="Priority level")
    status: str = Field(..., description="Task status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    user_id: int = Field(..., description="Owner user identifier")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Ensure ``priority`` is a valid ``Priority`` value.

        Args:
            v: The priority string.

        Returns:
            The original string if valid.

        Raises:
            ValueError: If ``v`` is not a valid ``Priority``.
        """
        if v not in Priority.__members__:
            raise ValueError(f"Invalid priority '{v}'. Expected one of: {', '.join(Priority.__members__)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure ``status`` is a valid ``Status`` value.

        Args:
            v: The status string.

        Returns:
            The original string if valid.

        Raises:
            ValueError: If ``v`` is not a valid ``Status``.
        """
        if v not in Status.__members__:
            raise ValueError(f"Invalid status '{v}'. Expected one of: {', '.join(Status.__members__)}")
        return v


class TaskUpdate(BaseModel):
    """Schema for partially updating a task.

    All fields are optional; only provided values will be updated.

    Args:
        title: New title for the task.
        description: New description.
        priority: New priority; must be a valid ``Priority`` if supplied.
        status: New status; must be a valid ``Status`` if supplied.

    Returns:
        An instance of ``TaskUpdate`` with validated update data.

    Raises:
        ValueError: If supplied ``priority`` or ``status`` are invalid.
    """

    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    priority: Optional[str] = Field(None, description="Updated priority (HIGH, MEDIUM, LOW)")
    status: Optional[str] = Field(None, description="Updated status (TODO, IN_PROGRESS, DONE)")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate optional ``priority`` against ``Priority`` enum.

        Args:
            v: The priority string or ``None``.

        Returns:
            The original value if valid or ``None``.

        Raises:
            ValueError: If ``v`` is not ``None`` and not a valid ``Priority``.
        """
        if v is not None and v not in Priority.__members__:
            raise ValueError(f"Invalid priority '{v}'. Expected one of: {', '.join(Priority.__members__)}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate optional ``status`` against ``Status`` enum.

        Args:
            v: The status string or ``None``.

        Returns:
            The original value if valid or ``None``.

        Raises:
            ValueError: If ``v`` is not ``None`` and not a valid ``Status``.
        """
        if v is not None and v not in Status.__members__:
            raise ValueError(f"Invalid status '{v}'. Expected one of: {', '.join(Status.__members__)}")
        return v