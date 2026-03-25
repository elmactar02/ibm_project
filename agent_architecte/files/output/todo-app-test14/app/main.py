from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient, Response
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings
import httpx

# Application configuration
settings = Settings()

# Constants derived from project context
PROJECT_NAME: str = "todo-app-test14"
TABLE_NAME: str = "task"

# Base URL for the remote database API
BASE_URL: str = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}"

app = FastAPI()


def _to_remote_enum(value: str | None) -> str | None:
    """
    Convert an enum value from the API schema (uppercase) to the remote API format (lowercase).

    Args:
        value: The enum value as a string.

    Returns:
        The enum value in lowercase, or None if value is None.
    """
    return value.lower() if value else None


def _from_remote_enum(value: str | None) -> str | None:
    """
    Convert an enum value from the remote API format (lowercase) to the API schema format (uppercase).

    Args:
        value: The enum value as a string.

    Returns:
        The enum value in uppercase, or None if value is None.
    """
    return value.upper() if value else None


def _convert_to_remote(data: dict) -> dict:
    """
    Convert task data to the format expected by the remote API.

    Args:
        data: The task data dictionary.

    Returns:
        A new dictionary with enum fields converted to lowercase.
    """
    converted = data.copy()
    if "priority" in converted:
        converted["priority"] = _to_remote_enum(converted["priority"])
    if "status" in converted:
        converted["status"] = _to_remote_enum(converted["status"])
    return converted


def _convert_from_remote(data: dict) -> dict:
    """
    Convert task data received from the remote API to the format expected by the API schema.

    Args:
        data: The task data dictionary.

    Returns:
        A new dictionary with enum fields converted to uppercase.
    """
    converted = data.copy()
    if "priority" in converted:
        converted["priority"] = _from_remote_enum(converted["priority"])
    if "status" in converted:
        converted["status"] = _from_remote_enum(converted["status"])
    return converted


async def _handle_remote_response(response: httpx.Response) -> dict:
    """
    Handle the HTTP response from the remote API.

    Args:
        response: The httpx.Response object.

    Returns:
        The JSON-decoded response data.

    Raises:
        HTTPException: If the remote API returns a non-success status code.
    """
    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Remote API error",
        )
    try:
        return response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse remote response: {exc}",
        ) from exc


@app.get("/tasks", response_model=list[TaskRead])
async def list_tasks() -> list[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        A list of TaskRead objects.
    """
    async with AsyncClient() as client:
        response = await client.get(BASE_URL)
    data = await _handle_remote_response(response)
    tasks = [_convert_from_remote(item) for item in data]
    return tasks


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: The task data to create.

    Returns:
        The created TaskRead object.
    """
    payload = _convert_to_remote(task.dict())
    async with AsyncClient() as client:
        response = await client.post(BASE_URL, json=payload)
    data = await _handle_remote_response(response)
    return _convert_from_remote(data)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a task by its ID.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The TaskRead object.
    """
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
    data = await _handle_remote_response(response)
    return _convert_from_remote(data)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: The ID of the task to update.
        task: The fields to update.

    Returns:
        The updated TaskRead object.
    """
    payload = _convert_to_remote(task.dict(exclude_unset=True))
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.put(url, json=payload)
    data = await _handle_remote_response(response)
    return _convert_from_remote(data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: The ID of the task to delete.

    Returns:
        None. Returns HTTP 204 on success.
    """
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Failed to delete task",
        )
    return None