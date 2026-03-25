from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings
from typing import Optional, List, Dict, Any

# Application settings
settings = Settings()

# Project configuration
PROJECT_NAME: str = "todo-app"

# Database schema (synchronized from 'todo-app-test9')
DB_SCHEMA: Dict[str, Any] = {
    "users": {
        "columns": [
            {"id": 0, "name": "id", "type": "INTEGER", "not_null": False, "default": None, "pk": True},
            {"id": 1, "name": "email", "type": "TEXT", "not_null": True, "default": None, "pk": False},
            {"id": 2, "name": "hashed_password", "type": "TEXT", "not_null": True, "default": None, "pk": False},
            {"id": 3, "name": "created_at", "type": "TEXT", "not_null": True, "default": "datetime('now')", "pk": False},
            {"id": 4, "name": "deleted_at", "type": "TEXT", "not_null": False, "default": "NULL", "pk": False},
        ]
    },
    "sqlite_sequence": {
        "columns": [
            {"id": 0, "name": "name", "type": "", "not_null": False, "default": None, "pk": False},
            {"id": 1, "name": "seq", "type": "", "not_null": False, "default": None, "pk": False},
        ]
    },
    "tasks": {
        "columns": [
            {"id": 0, "name": "id", "type": "INTEGER", "not_null": False, "default": None, "pk": True},
            {"id": 1, "name": "title", "type": "TEXT", "not_null": True, "default": None, "pk": False},
            {"id": 2, "name": "description", "type": "TEXT", "not_null": False, "default": "NULL", "pk": False},
            {"id": 3, "name": "status", "type": "TEXT", "not_null": True, "default": "'todo'", "pk": False},
            {"id": 4, "name": "priority", "type": "TEXT", "not_null": True, "default": "'medium'", "pk": False},
            {"id": 5, "name": "created_at", "type": "TEXT", "not_null": True, "default": "datetime('now')", "pk": False},
            {"id": 6, "name": "updated_at", "type": "TEXT", "not_null": False, "default": "datetime('now')", "pk": False},
            {"id": 7, "name": "user_id", "type": "INTEGER", "not_null": True, "default": None, "pk": False},
            {"id": 8, "name": "deleted_at", "type": "TEXT", "not_null": False, "default": "NULL", "pk": False},
        ],
        "foreign_keys": [
            {"id": 0, "seq": 0, "table": "users", "from": "user_id", "to": "id", "on_delete": "NO ACTION", "on_update": "CASCADE"},
        ],
    },
}

# Dynamically determine the tasks table name from the schema
TABLE_NAME: str = next((name for name in DB_SCHEMA if name == "tasks"), None)
if TABLE_NAME is None:
    raise ValueError("Tasks table not found in database schema.")

app = FastAPI()


def _build_url(path: str) -> str:
    """
    Construct the full URL for the remote database API.

    Args:
        path: The path after the base URL.

    Returns:
        The full URL string.
    """
    return f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}{path}"


async def _handle_response(response: Any) -> Any:
    """
    Handle the HTTP response from the remote API.

    Args:
        response: The httpx.Response object.

    Returns:
        The JSON-decoded response data.

    Raises:
        HTTPException: If the response status is not 200-299.
    """
    if 200 <= response.status_code < 300:
        return response.json()
    try:
        detail = response.json()
    except Exception:
        detail = response.text
    raise HTTPException(
        status_code=response.status_code,
        detail=detail,
    )


@app.get("/tasks", response_model=List[TaskRead])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[TaskRead]:
    """
    Retrieve a list of tasks, optionally filtered by status and priority.

    Args:
        status: Optional status filter (e.g., "TODO").
        priority: Optional priority filter (e.g., "HIGH").

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If the remote API call fails.
    """
    params: Dict[str, str] = {}
    if status:
        params["status"] = status.lower()
    if priority:
        params["priority"] = priority.lower()

    async with AsyncClient() as client:
        response = await client.get(_build_url("/"), params=params)
        data = await _handle_response(response)
        return data


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: The TaskCreate payload.

    Returns:
        The created TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    payload = task.dict()
    if payload.get("priority"):
        payload["priority"] = payload["priority"].lower()
    if payload.get("status"):
        payload["status"] = payload["status"].lower()

    async with AsyncClient() as client:
        response = await client.post(_build_url("/"), json=payload)
        data = await _handle_response(response)
        return data


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a single task by ID.

    Args:
        task_id: The ID of the task.

    Returns:
        The TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    async with AsyncClient() as client:
        response = await client.get(_build_url(f"/{task_id}"))
        data = await _handle_response(response)
        return data


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: The ID of the task to update.
        task: The TaskUpdate payload.

    Returns:
        The updated TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    payload = task.dict(exclude_unset=True)
    if payload.get("priority"):
        payload["priority"] = payload["priority"].lower()
    if payload.get("status"):
        payload["status"] = payload["status"].lower()

    async with AsyncClient() as client:
        response = await client.put(_build_url(f"/{task_id}"), json=payload)
        data = await _handle_response(response)
        return data


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by ID.

    Args:
        task_id: The ID of the task to delete.

    Raises:
        HTTPException: If the remote API call fails.
    """
    async with AsyncClient() as client:
        response = await client.delete(_build_url(f"/{task_id}"))
        await _handle_response(response)
        return None
