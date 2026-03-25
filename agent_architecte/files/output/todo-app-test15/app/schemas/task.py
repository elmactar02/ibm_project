from enum import Enum

from pydantic import BaseModel


class Priority(str, Enum):
    """Enumeration of task priority levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    """Enumeration of task status values."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str
    description: str
    priority: str
    status: str


class TaskRead(BaseModel):
    """Schema for reading task data."""
    id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    user_id: int


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None