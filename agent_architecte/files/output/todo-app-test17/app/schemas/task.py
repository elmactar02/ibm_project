from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Status(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    status: str


class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    user_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

