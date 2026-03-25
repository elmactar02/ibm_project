from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from typing import List, Optional

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()
app = FastAPI(title="Todo App Proxy", version="1.0.0")

PROJECT_NAME = "todo-app-test25"
TASK_TABLE_NAME = "Task"


def _build_url(task_id: Optional[int] = None) -> str:
    """
    Construct the remote API URL for task operations.

    Args:
        task_id: Optional identifier of a specific task.

    Returns:
        Fully qualified URL as a string.
    """
    base = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TASK_TABLE_NAME}"
    return f"{base}/{task_id}" if task_id is not None else base


def _convert_item(item: dict) -> TaskRead:
    """
    Convert a raw dictionary from the remote API into a TaskRead model.

    Args:
        item: Dictionary containing task fields.

    Returns:
        TaskRead instance.

    Raises:
        pydantic.ValidationError: If the dictionary does not match the schema.
    """
    return TaskRead(**item)


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks() -> List[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        List of TaskRead objects.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url()
    async with AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch tasks: {response.text}",
        )
    data = response.json()
    rows = data.get("rows", [])
    return [_convert_item(row) for row in rows]


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: TaskCreate payload.

    Returns:
        Created TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url()
    # Convert to dict and remove None values before sending to API
    task_data = task.dict()
    task_data = {k: v for k, v in task_data.items() if v is not None}
    async with AsyncClient() as client:
        response = await client.post(url, json=task_data)
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create task: {response.text}",
        )
    return _convert_item(response.json())


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a single task by its ID.

    Args:
        task_id: Identifier of the task.

    Returns:
        TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url(task_id)
    async with AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to retrieve task {task_id}: {response.text}",
        )
    return _convert_item(response.json())


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: Identifier of the task to update.
        task: TaskUpdate payload with fields to modify.

    Returns:
        Updated TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url(task_id)
    # Convert to dict, exclude unset fields and remove None values
    task_data = task.dict(exclude_unset=True)
    task_data = {k: v for k, v in task_data.items() if v is not None}
    async with AsyncClient() as client:
        response = await client.put(url, json=task_data)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update task {task_id}: {response.text}",
        )
    return _convert_item(response.json())


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: Identifier of the task to delete.

    Returns:
        None. Responds with HTTP 204 No Content on success.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url(task_id)
    async with AsyncClient() as client:
        response = await client.delete(url)
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete task {task_id}: {response.text}",
        )
    return None