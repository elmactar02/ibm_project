from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


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
        description: Detailed description; may be omitted.
        priority: Priority level of the task.
        status: Current status of the task.

    Raises:
        ValueError: If ``title`` is empty or only whitespace.
    """

    title: str = Field(..., description="Short title of the task")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the task"
    )
    priority: Priority = Field(..., description="Priority level of the task")
    status: Status = Field(..., description="Current status of the task")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure the title is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("title must be a non‑empty string")
        return v


class TaskRead(BaseModel):
    """Schema for reading task data from the API.

    Args:
        id: Primary key of the task.
        title: Short title of the task.
        description: Detailed description; may be ``None``.
        priority: Priority level of the task.
        status: Current status of the task.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        user_id: Identifier of the owning user.
    """

    id: int = Field(..., description="Primary key of the task")
    title: str = Field(..., description="Short title of the task")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the task"
    )
    priority: Priority = Field(..., description="Priority level of the task")
    status: Status = Field(..., description="Current status of the task")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    user_id: int = Field(..., description="Identifier of the owning user")

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Schema for updating an existing task.

    All fields are optional; only provided fields will be updated.

    Args:
        title: New title for the task.
        description: New description for the task.
        priority: New priority level.
        status: New status.

    Raises:
        ValueError: If ``title`` is provided but empty or whitespace only.
    """

    title: Optional[str] = Field(
        default=None, description="New title for the task"
    )
    description: Optional[str] = Field(
        default=None, description="New description for the task"
    )
    priority: Optional[Priority] = Field(
        default=None, description="New priority level"
    )
    status: Optional[Status] = Field(
        default=None, description="New status"
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if it is provided."""
        if v is not None and not v.strip():
            raise ValueError("title must be a non‑empty string when provided")
        return v

__all__ = [
    "Priority",
    "Status",
    "TaskCreate",
    "TaskRead",
    "TaskUpdate",
]