from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from typing import List

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

# Application settings
settings = Settings()

# Project and table configuration
PROJECT_NAME: str = "todo-app-test17"
TABLE_NAME: str = "tasks"

# Base URL for the remote database API
BASE_REMOTE_URL: str = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}"


app = FastAPI()


def _convert_to_lowercase(value: str) -> str:
    """Convert a string value to lowercase."""
    return value.lower()


def _convert_to_uppercase(value: str) -> str:
    """Convert a string value to uppercase."""
    return value.upper()


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks(status_filter: Status | None = None, priority: Priority | None = None) -> List[TaskRead]:
    """
    Retrieve a list of tasks, optionally filtered by status and priority.

    Args
    ----
    status_filter : Status, optional
        Filter tasks by status.
    priority : Priority, optional
        Filter tasks by priority.

    Returns
    -------
    List[TaskRead]
        A list of tasks matching the filter criteria.

    Raises
    ------
    HTTPException
        If the remote API call fails.
    """
    params = {}
    if status_filter is not None:
        params["status"] = _convert_to_lowercase(status_filter.value)
    if priority is not None:
        params["priority"] = _convert_to_lowercase(priority.value)

    async with AsyncClient() as client:
        response = await client.get(BASE_REMOTE_URL, params=params)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        tasks_data = response.json()
        for task in tasks_data:
            task["priority"] = _convert_to_uppercase(task["priority"])
            task["status"] = _convert_to_uppercase(task["status"])
        return tasks_data


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args
    ----
    task : TaskCreate
        The task data to create.

    Returns
    -------
    TaskRead
        The created task.

    Raises
    ------
    HTTPException
        If the remote API call fails.
    """
    payload = {
        "title": task.title,
        "description": task.description,
        "priority": _convert_to_lowercase(task.priority),
        "status": _convert_to_lowercase(task.status),
    }

    async with AsyncClient() as client:
        response = await client.post(BASE_REMOTE_URL, json=payload)
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        task_data = response.json()
        task_data["priority"] = _convert_to_uppercase(task_data["priority"])
        task_data["status"] = _convert_to_uppercase(task_data["status"])
        return task_data


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a task by its ID.

    Args
    ----
    task_id : int
        The ID of the task to retrieve.

    Returns
    -------
    TaskRead
        The requested task.

    Raises
    ------
    HTTPException
        If the remote API call fails.
    """
    url = f"{BASE_REMOTE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        task_data = response.json()
        task_data["priority"] = _convert_to_uppercase(task_data["priority"])
        task_data["status"] = _convert_to_uppercase(task_data["status"])
        return task_data


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args
    ----
    task_id : int
        The ID of the task to update.
    task : TaskUpdate
        The fields to update.

    Returns
    -------
    TaskRead
        The updated task.

    Raises
    ------
    HTTPException
        If the remote API call fails.
    """
    payload = {}
    if task.title is not None:
        payload["title"] = task.title
    if task.description is not None:
        payload["description"] = task.description
    if task.priority is not None:
        payload["priority"] = _convert_to_lowercase(task.priority)
    if task.status is not None:
        payload["status"] = _convert_to_lowercase(task.status)

    url = f"{BASE_REMOTE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.put(url, json=payload)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        task_data = response.json()
        task_data["priority"] = _convert_to_uppercase(task_data["priority"])
        task_data["status"] = _convert_to_uppercase(task_data["status"])
        return task_data


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args
    ----
    task_id : int
        The ID of the task to delete.

    Raises
    ------
    HTTPException
        If the remote API call fails.
    """
    url = f"{BASE_REMOTE_URL}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
        if response.status_code != status.HTTP_204_NO_CONTENT:
            raise HTTPException(status_code=response.status_code, detail=response.text)