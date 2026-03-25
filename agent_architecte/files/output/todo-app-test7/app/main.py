from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

app = FastAPI()
settings = Settings()
PROJECT_NAME = "todo-app"
BASE_URL = f"{settings.DB_API_URL}/databases/{PROJECT_NAME}/data/tasks"

client: AsyncClient | None = None


@app.on_event("startup")
async def startup_event() -> None:
    """Create a shared AsyncClient on startup."""
    global client
    client = AsyncClient()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Close the shared AsyncClient on shutdown."""
    if client:
        await client.aclose()


async def _handle_response(response: "httpx.Response") -> dict:
    """Validate and parse the HTTP response from the remote API.

    Args:
        response: The httpx Response object.

    Returns:
        The JSON-decoded body of the response.

    Raises:
        HTTPException: If the response status code indicates an error.
    """
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Remote API error",
        )
    return response.json()


@app.get("/tasks/", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def get_tasks(
    status_filter: Status | None = None,
    priority_filter: Priority | None = None,
) -> list[TaskRead]:
    """Retrieve a list of tasks with optional status and priority filters.

    Args:
        status_filter: Optional status to filter tasks.
        priority_filter: Optional priority to filter tasks.

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If the remote API request fails.
    """
    params = {}
    if status_filter:
        params["status"] = status_filter.value
    if priority_filter:
        params["priority"] = priority_filter.value

    response = await client.get(BASE_URL, params=params)
    data = await _handle_response(response)
    return [TaskRead(**item) for item in data]


@app.post("/tasks/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """Create a new task.

    Args:
        task: The task data to create.

    Returns:
        The created TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    payload = task.dict()
    response = await client.post(BASE_URL, json=payload)
    data = await _handle_response(response)
    return TaskRead(**data)


@app.put("/tasks/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """Update an existing task.

    Args:
        task_id: The ID of the task to update.
        task: The updated task data.

    Returns:
        The updated TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    payload = task.dict(exclude_unset=True)
    url = f"{BASE_URL}/{task_id}"
    response = await client.put(url, json=payload)
    data = await _handle_response(response)
    return TaskRead(**data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """Delete a task.

    Args:
        task_id: The ID of the task to delete.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = f"{BASE_URL}/{task_id}"
    response = await client.delete(url)
    if response.status_code != status.HTTP_204_NO_CONTENT:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text or "Failed to delete task",
        )
    return None