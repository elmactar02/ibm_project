from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings
from typing import List, Optional

settings = Settings()
project_name = "todo-app-test16"
table_name = "tasks"
base_url = f"{settings.db_api_url}/databases/{project_name}/data/{table_name}"


def _enum_to_lower(value: str) -> str:
    """Convert enum string to lowercase."""
    return value.lower()


def _enum_to_upper(value: str) -> str:
    """Convert enum string to uppercase."""
    return value.upper()


app = FastAPI()


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks(
    status_filter: Optional[Status] = None,
    priority: Optional[Priority] = None,
) -> List[TaskRead]:
    """
    Retrieve a list of tasks with optional status and priority filters.

    Args:
        status_filter: Optional status filter.
        priority: Optional priority filter.

    Returns:
        A list of TaskRead objects.

    Raises:
        HTTPException: If the remote API request fails.
    """
    params = {}
    if status_filter:
        params["status"] = _enum_to_lower(status_filter.value)
    if priority:
        params["priority"] = _enum_to_lower(priority.value)

    async with AsyncClient() as client:
        response = await client.get(base_url, params=params)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        tasks_data = response.json()
        tasks = []
        for item in tasks_data:
            item["priority"] = _enum_to_upper(item["priority"])
            item["status"] = _enum_to_upper(item["status"])
            tasks.append(TaskRead(**item))
        return tasks


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: TaskCreate schema containing task details.

    Returns:
        The created TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    payload = task.dict()
    payload["priority"] = _enum_to_lower(payload["priority"].value)
    payload["status"] = _enum_to_lower(payload["status"].value)

    async with AsyncClient() as client:
        response = await client.post(base_url, json=payload)
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        data = response.json()
        data["priority"] = _enum_to_upper(data["priority"])
        data["status"] = _enum_to_upper(data["status"])
        return TaskRead(**data)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a task by its ID.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        data = response.json()
        data["priority"] = _enum_to_upper(data["priority"])
        data["status"] = _enum_to_upper(data["status"])
        return TaskRead(**data)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: The ID of the task to update.
        task: TaskUpdate schema with fields to modify.

    Returns:
        The updated TaskRead object.

    Raises:
        HTTPException: If the remote API request fails.
    """
    payload = task.dict(exclude_unset=True)
    if "priority" in payload:
        payload["priority"] = _enum_to_lower(payload["priority"].value)
    if "status" in payload:
        payload["status"] = _enum_to_lower(payload["status"].value)

    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.put(url, json=payload)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
        data = response.json()
        data["priority"] = _enum_to_upper(data["priority"])
        data["status"] = _enum_to_upper(data["status"])
        return TaskRead(**data)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: The ID of the task to delete.

    Raises:
        HTTPException: If the remote API request fails.
    """
    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
        if response.status_code != status.HTTP_204_NO_CONTENT:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )
    return None