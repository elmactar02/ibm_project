from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient, Response
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()
app = FastAPI()

PROJECT_NAME = "todo-app-test22"
TABLE_NAME = "task"


def _enum_to_remote(value: str) -> str:
    """Convert internal enum string (e.g., ``HIGH``) to remote API format (e.g., ``high``).

    Args:
        value: Enum value from the Pydantic schema.

    Returns:
        Lower‑case representation expected by the remote API.
    """
    return value.lower()


def _enum_from_remote(value: str) -> str:
    """Convert remote API enum string (e.g., ``high``) to internal format (e.g., ``HIGH``).

    Args:
        value: Enum value returned by the remote API.

    Returns:
        Upper‑case representation used by the Pydantic schemas.
    """
    return value.upper()


async def _request(
    method: str,
    path: str,
    *,
    json: dict | None = None,
) -> Response:
    """Perform an HTTP request against the remote database API.

    Args:
        method: HTTP method name (``GET``, ``POST`` …).
        path: Path relative to the remote API base URL.
        json: Optional JSON payload for ``POST``/``PUT`` requests.

    Returns:
        The :class:`httpx.Response` object.

    Raises:
        HTTPException: If the remote service returns a non‑2xx status.
    """
    async with AsyncClient(base_url=settings.db_api_url) as client:
        response = await client.request(method, path, json=json)
    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Remote API error",
        )
    return response


@app.get("/tasks", response_model=list[TaskRead])
async def list_tasks() -> list[TaskRead]:
    """Retrieve all tasks.

    Returns:
        A list of :class:`TaskRead` objects.

    Raises:
        HTTPException: If the remote API request fails.
    """
    path = f"/databases/{PROJECT_NAME}/data/{TABLE_NAME}"
    response = await _request("GET", path)
    raw_tasks: list[dict] = response.json()
    tasks = []
    for raw in raw_tasks:
        raw["priority"] = _enum_from_remote(raw.get("priority", ""))
        raw["status"] = _enum_from_remote(raw.get("status", ""))
        tasks.append(TaskRead(**raw))
    return tasks


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """Create a new task.

    Args:
        task: Data required to create the task.

    Returns:
        The created :class:`TaskRead` object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    payload = task.model_dump()
    if "priority" in payload:
        payload["priority"] = _enum_to_remote(payload["priority"])
    if "status" in payload:
        payload["status"] = _enum_to_remote(payload["status"])
    path = f"/databases/{PROJECT_NAME}/data/{TABLE_NAME}"
    response = await _request("POST", path, json=payload)
    raw = response.json()
    raw["priority"] = _enum_from_remote(raw.get("priority", ""))
    raw["status"] = _enum_from_remote(raw.get("status", ""))
    return TaskRead(**raw)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """Retrieve a single task by its identifier.

    Args:
        task_id: Identifier of the task to retrieve.

    Returns:
        The requested :class:`TaskRead` object.

    Raises:
        HTTPException: If the task does not exist or the remote request fails.
    """
    path = f"/databases/{PROJECT_NAME}/data/{TABLE_NAME}/{task_id}"
    response = await _request("GET", path)
    raw = response.json()
    raw["priority"] = _enum_from_remote(raw.get("priority", ""))
    raw["status"] = _enum_from_remote(raw.get("status", ""))
    return TaskRead(**raw)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """Update an existing task.

    Args:
        task_id: Identifier of the task to update.
        task: Fields to be updated.

    Returns:
        The updated :class:`TaskRead` object.

    Raises:
        HTTPException: If the task does not exist or the remote request fails.
    """
    payload = task.model_dump(exclude_unset=True)
    if "priority" in payload:
        payload["priority"] = _enum_to_remote(payload["priority"])
    if "status" in payload:
        payload["status"] = _enum_to_remote(payload["status"])
    path = f"/databases/{PROJECT_NAME}/data/{TABLE_NAME}/{task_id}"
    response = await _request("PUT", path, json=payload)
    raw = response.json()
    raw["priority"] = _enum_from_remote(raw.get("priority", ""))
    raw["status"] = _enum_from_remote(raw.get("status", ""))
    return TaskRead(**raw)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """Delete a task.

    Args:
        task_id: Identifier of the task to delete.

    Raises:
        HTTPException: If the task does not exist or the remote request fails.
    """
    path = f"/databases/{PROJECT_NAME}/data/{TABLE_NAME}/{task_id}"
    await _request("DELETE", path)
    return None