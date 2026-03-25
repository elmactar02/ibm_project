from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from typing import List

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()
app = FastAPI(title="Task Proxy API")

PROJECT_NAME = "todo-app-test23"
REMOTE_TABLE = "tasks"


def _convert_task(data: dict) -> TaskRead:
    """
    Convert a raw task dictionary from the remote API into a ``TaskRead`` instance.

    Args:
        data: Dictionary containing task fields as returned by the remote API.

    Returns:
        A ``TaskRead`` model with ``priority`` and ``status`` as enum instances.

    Raises:
        KeyError: If required keys are missing in ``data``.
        ValueError: If enum conversion fails.
    """
    try:
        data["priority"] = Priority[data["priority"]]
        data["status"] = Status[data["status"]]
    except KeyError as exc:
        raise ValueError(f"Missing required task field: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Enum conversion error: {exc}") from exc

    return TaskRead(**data)


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks() -> List[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        A list of ``TaskRead`` objects.

    Raises:
        HTTPException: If the remote API request fails or task conversion fails.
    """
    url = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{REMOTE_TABLE}"
    async with AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch tasks: {response.text}",
        )

    raw_tasks: List[dict] = response.json()
    tasks: List[TaskRead] = []
    for raw in raw_tasks:
        try:
            tasks.append(_convert_task(raw))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
    return tasks


@app.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: ``TaskCreate`` payload containing task details.

    Returns:
        The created ``TaskRead`` object.

    Raises:
        HTTPException: If the remote API request fails or task conversion fails.
    """
    url = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{REMOTE_TABLE}"
    async with AsyncClient() as client:
        response = await client.post(url, json=task.model_dump())

    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create task: {response.text}",
        )

    raw_task: dict = response.json()
    try:
        return _convert_task(raw_task)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a single task by its identifier.

    Args:
        task_id: Identifier of the task to retrieve.

    Returns:
        The ``TaskRead`` representation of the requested task.

    Raises:
        HTTPException: If the task is not found, the remote API request fails,
            or task conversion fails.
    """
    url = (
        f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{REMOTE_TABLE}/{task_id}"
    )
    async with AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to fetch task: {response.text}",
        )

    raw_task: dict = response.json()
    try:
        return _convert_task(raw_task)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: Identifier of the task to update.
        task: ``TaskUpdate`` payload with fields to modify.

    Returns:
        The updated ``TaskRead`` object.

    Raises:
        HTTPException: If the task is not found, the remote API request fails,
            or task conversion fails.
    """
    url = (
        f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{REMOTE_TABLE}/{task_id}"
    )
    async with AsyncClient() as client:
        response = await client.put(url, json=task.model_dump(exclude_unset=True))

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_202_ACCEPTED):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to update task: {response.text}",
        )

    raw_task: dict = response.json()
    try:
        return _convert_task(raw_task)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task.

    Args:
        task_id: Identifier of the task to delete.

    Raises:
        HTTPException: If the task is not found or the remote API request fails.
    """
    url = (
        f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{REMOTE_TABLE}/{task_id}"
    )
    async with AsyncClient() as client:
        response = await client.delete(url)

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to delete task: {response.text}",
        )
    return None