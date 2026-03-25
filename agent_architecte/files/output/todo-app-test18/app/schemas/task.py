from enum import Enum
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
    priority: Priority
    status: Status


class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    created_at: str
    updated_at: str
    user_id: int


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    status: Status | None = None