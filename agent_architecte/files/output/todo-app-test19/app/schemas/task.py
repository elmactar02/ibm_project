from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Priority(str, Enum):
    """Priority levels for a task."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    """Status of a task."""
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
    """Schema for reading a task."""
    id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    user_id: int


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

