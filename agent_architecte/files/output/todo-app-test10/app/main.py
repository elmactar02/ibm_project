from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

# Application configuration
settings = Settings()

# Constants derived from the database schema
PROJECT_NAME = "todo-app"
TABLE_NAME = "tasks"


def _normalize_task(data: dict) -> dict:
    """
    Convert enum values from lowercase to uppercase for priority and status.

    Args:
        data: Raw task data from the remote API.

    Returns:
        dict: Normalized task data with uppercase enum values.
    """
    if "priority" in data and isinstance(data["priority"], str):
        data["priority"] = data["priority"].upper()
    if "status" in data and isinstance(data["status"], str):
        data["status"] = data["status"].upper()
    return data


def _build_url(path: str = "") -> str:
    """
    Construct the full URL for the remote database API.

    Args:
        path: Additional path to append to the base URL.

    Returns:
        str: Full URL string.
    """
    return f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}{path}"


app = FastAPI()


@app.get("/tasks", response_model=list[TaskRead])
async def list_tasks() -> list[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        List[TaskRead]: A list of task objects.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url()
    async with AsyncClient() as client:
        try:
            resp = await client.get(url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to remote API: {exc}",
            )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Remote API error: {resp.status_code}",
        )
    tasks_raw = resp.json()
    tasks = [_normalize_task(task) for task in tasks_raw]
    return [TaskRead.parse_obj(task) for task in tasks]


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: TaskCreate schema containing task details.

    Returns:
        TaskRead: The created task object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = _build_url()
    payload = task.dict()
    # Ensure enum values are uppercase before sending
    payload["priority"] = payload["priority"].upper()
    payload["status"] = payload["status"].upper()
    async with AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to remote API: {exc}",
            )
    if resp.status_code not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Remote API error: {resp.status_code}",
        )
    task_data = _normalize_task(resp.json())
    return TaskRead.parse_obj(task_data)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a specific task by ID.

    Args:
        task_id: Identifier of the task.

    Returns:
        TaskRead: The requested task object.

    Raises:
        HTTPException: If the remote API request fails or task not found.
    """
    url = _build_url(f"/{task_id}")
    async with AsyncClient() as client:
        try:
            resp = await client.get(url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to remote API: {exc}",
            )
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Remote API error: {resp.status_code}",
        )
    task_data = _normalize_task(resp.json())
    return TaskRead.parse_obj(task_data)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: Identifier of the task to update.
        task: TaskUpdate schema containing fields to modify.

    Returns:
        TaskRead: The updated task object.

    Raises:
        HTTPException: If the remote API request fails or task not found.
    """
    url = _build_url(f"/{task_id}")
    payload = task.dict(exclude_unset=True)
    # Convert enum values to uppercase if present
    if "priority" in payload:
        payload["priority"] = payload["priority"].upper()
    if "status" in payload:
        payload["status"] = payload["status"].upper()
    async with AsyncClient() as client:
        try:
            resp = await client.put(url, json=payload)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to remote API: {exc}",
            )
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Remote API error: {resp.status_code}",
        )
    task_data = _normalize_task(resp.json())
    return TaskRead.parse_obj(task_data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by ID.

    Args:
        task_id: Identifier of the task to delete.

    Raises:
        HTTPException: If the remote API request fails or task not found.
    """
    url = _build_url(f"/{task_id}")
    async with AsyncClient() as client:
        try:
            resp = await client.delete(url)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to remote API: {exc}",
            )
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if resp.status_code not in (200, 204):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Remote API error: {resp.status_code}",
        )
    return None

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)