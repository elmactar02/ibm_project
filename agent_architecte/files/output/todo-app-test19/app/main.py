from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from typing import List, Dict, Any

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings
from app.db_tables import db_tables


# Application settings
settings = Settings()

# Project and table configuration
PROJECT_NAME = "todo-app-test19"
TABLE_NAME = db_tables[0] if db_tables else "tasks"

# Base URL for the remote database API
BASE_URL = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}"

app = FastAPI()


def _to_lowercase(value: str) -> str:
    """
    Convert a string enum value to lowercase.

    Args:
        value: The string to convert.

    Returns:
        The lowercase string.
    """
    return value.lower()


def _to_uppercase(value: str) -> str:
    """
    Convert a string enum value to uppercase.

    Args:
        value: The string to convert.

    Returns:
        The uppercase string.
    """
    return value.upper()


def _convert_task_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert priority and status fields from lowercase to uppercase in the task data.

    Args:
        data: The task data dictionary.

    Returns:
        The converted task data dictionary.
    """
    if "priority" in data:
        data["priority"] = _to_uppercase(data["priority"])
    if "status" in data:
        data["status"] = _to_uppercase(data["status"])
    return data


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks() -> List[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If the remote API call fails.
    """
    async with AsyncClient() as client:
        response = await client.get(BASE_URL)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch tasks: {response.text}",
        )
    tasks = response.json()
    converted = [_convert_task_response(task) for task in tasks]
    return converted


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
    payload["priority"] = _to_lowercase(payload["priority"])
    payload["status"] = _to_lowercase(payload["status"])
    async with AsyncClient() as client:
        response = await client.post(BASE_URL, json=payload)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create task: {response.text}",
        )
    created = response.json()
    return _convert_task_response(created)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a specific task by ID.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Task not found: {response.text}",
        )
    task = response.json()
    return _convert_task_response(task)


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
    if "priority" in payload:
        payload["priority"] = _to_lowercase(payload["priority"])
    if "status" in payload:
        payload["status"] = _to_lowercase(payload["status"])
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.put(url, json=payload)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update task: {response.text}",
        )
    updated = response.json()
    return _convert_task_response(updated)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by ID.

    Args:
        task_id: The ID of the task to delete.

    Raises:
        HTTPException: If the remote API call fails.
    """
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
    if response.status_code != status.HTTP_204_NO_CONTENT:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete task: {response.text}",
        )
    return None

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)