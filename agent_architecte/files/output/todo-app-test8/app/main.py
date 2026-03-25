from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()
BASE_URL: str = settings.db_api_url
PROJECT_NAME: str = "todo-app"
TABLE: str = "tasks"
ENDPOINT: str = f"{BASE_URL}/databases/{PROJECT_NAME}/data/{TABLE}"

app = FastAPI()


def _normalize_task(data: dict) -> TaskRead:
    """
    Convert task data from the remote API to the TaskRead schema.
    The remote API returns priority and status in uppercase; this function
    converts them to lowercase to match the frontend expectations.

    Args:
        data: Dictionary containing task fields from the remote API.

    Returns:
        TaskRead: Pydantic model instance with normalized values.
    """
    data = data.copy()
    if "priority" in data and isinstance(data["priority"], str):
        data["priority"] = data["priority"].lower()
    if "status" in data and isinstance(data["status"], str):
        data["status"] = data["status"].lower()
    return TaskRead(**data)


@app.get("/tasks", response_model=list[TaskRead])
async def get_tasks() -> list[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        List[TaskRead]: A list of task objects.

    Raises:
        HTTPException: If the remote API call fails.
    """
    async with AsyncClient() as client:
        response = await client.get(ENDPOINT)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch tasks from remote API",
        )
    tasks_data = response.json()
    return [_normalize_task(task) for task in tasks_data]


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: TaskCreate schema containing task details.

    Returns:
        TaskRead: The created task object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    task_dict = task.dict()
    if "priority" in task_dict and isinstance(task_dict["priority"], str):
        task_dict["priority"] = task_dict["priority"].upper()
    if "status" in task_dict and isinstance(task_dict["status"], str):
        task_dict["status"] = task_dict["status"].upper()
    async with AsyncClient() as client:
        response = await client.post(ENDPOINT, json=task_dict)
    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to create task in remote API",
        )
    task_data = response.json()
    return _normalize_task(task_data)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a specific task by its ID.

    Args:
        task_id: Identifier of the task.

    Returns:
        TaskRead: The task object.

    Raises:
        HTTPException: If the task is not found or remote API call fails.
    """
    url = f"{ENDPOINT}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch task from remote API",
        )
    task_data = response.json()
    return _normalize_task(task_data)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: Identifier of the task to update.
        task: TaskUpdate schema with fields to modify.

    Returns:
        TaskRead: The updated task object.

    Raises:
        HTTPException: If the task is not found or remote API call fails.
    """
    url = f"{ENDPOINT}/{task_id}"
    update_dict = {k: v for k, v in task.dict(exclude_unset=True).items() if v is not None}
    if "priority" in update_dict and isinstance(update_dict["priority"], str):
        update_dict["priority"] = update_dict["priority"].upper()
    if "status" in update_dict and isinstance(update_dict["status"], str):
        update_dict["status"] = update_dict["status"].upper()
    async with AsyncClient() as client:
        response = await client.put(url, json=update_dict)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to update task in remote API",
        )
    task_data = response.json()
    return _normalize_task(task_data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: Identifier of the task to delete.

    Raises:
        HTTPException: If the task is not found or remote API call fails.
    """
    url = f"{ENDPOINT}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    if response.status_code != status.HTTP_204_NO_CONTENT:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to delete task in remote API",
        )
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)