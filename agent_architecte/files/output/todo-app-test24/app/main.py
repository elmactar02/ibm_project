from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient, Response
from typing import List

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()
app = FastAPI(title="Task Proxy API")

PROJECT_NAME = "todo-app-test24"
TASK_TABLE_NAME = "task"


def _build_url(task_id: int | None = None) -> str:
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
    Convert a raw task dictionary from the remote API into a validated TaskRead model.

    Args:
        item: Dictionary containing task fields.

    Returns:
        A TaskRead instance.

    Raises:
        HTTPException: If item is missing required fields.
    """
    if not isinstance(item, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected dict, got " + type(item).__name__,
        )
    return TaskRead(**item)


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks() -> List[TaskRead]:
    """
    Retrieve all tasks from the remote database API.

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If the remote API request fails or returns an unexpected status.
    """
    url = _build_url()
    async with AsyncClient() as client:
        response: Response = await client.get(url)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch tasks: {response.text}",
        )
    data: dict = response.json()
    # API returns {"rows": [...], "count": N, ...}
    raw_list: List[dict] = data.get("rows", [])
    result: List[TaskRead] = []
    for item in raw_list:
        result.append(_convert_item(item))
    return result


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task by forwarding the request to the remote API.

    Args:
        task: ``TaskCreate`` payload validated by Pydantic.

    Returns:
        The created task as a ``TaskRead`` instance.

    Raises:
        HTTPException: If the remote API returns an error or enum conversion fails.
    """
    url = _build_url()
    async with AsyncClient() as client:
        response: Response = await client.post(url, json=task.dict())
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create task: {response.text}",
        )
    raw_item: dict = response.json()
    return _convert_item(raw_item)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a single task by its identifier.

    Args:
        task_id: Identifier of the task to fetch.

    Returns:
        The requested task as a ``TaskRead`` instance.

    Raises:
        HTTPException: If the task is not found or remote API returns an error.
    """
    url = _build_url(task_id)
    async with AsyncClient() as client:
        response: Response = await client.get(url)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to retrieve task: {response.text}",
        )
    raw_item: dict = response.json()
    return _convert_item(raw_item)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task with the provided fields.

    Args:
        task_id: Identifier of the task to update.
        task: ``TaskUpdate`` payload containing fields to modify.

    Returns:
        The updated task as a ``TaskRead`` instance.

    Raises:
        HTTPException: If the remote API returns an error or enum conversion fails.
    """
    url = _build_url(task_id)
    async with AsyncClient() as client:
        response: Response = await client.put(url, json=task.dict(exclude_unset=True))
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update task: {response.text}",
        )
    raw_item: dict = response.json()
    return _convert_item(raw_item)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its identifier.

    Args:
        task_id: Identifier of the task to delete.

    Raises:
        HTTPException: If the remote API returns an error.
    """
    url = _build_url(task_id)
    async with AsyncClient() as client:
        response: Response = await client.delete(url)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code != status.HTTP_204_NO_CONTENT:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete task: {response.text}",
        )
    return None