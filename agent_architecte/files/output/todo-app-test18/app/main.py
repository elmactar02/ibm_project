from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from typing import List

from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings


settings = Settings()
app = FastAPI()

project_name: str = "todo-app-test18"
table_name: str = "tasks"
base_url: str = f"{settings.db_api_url}/databases/{project_name}/data/{table_name}"


def _normalize_task(task: dict) -> dict:
    """
    Convert priority and status values from lower-case to upper-case
    to match the Pydantic enum definitions.

    Args:
        task: A dictionary representing a task as returned by the remote API.

    Returns:
        The same dictionary with 'priority' and 'status' values upper‑cased.
    """
    if "priority" in task and isinstance(task["priority"], str):
        task["priority"] = task["priority"].upper()
    if "status" in task and isinstance(task["status"], str):
        task["status"] = task["status"].upper()
    return task


@app.get("/tasks", response_model=List[TaskRead])
async def list_tasks() -> List[TaskRead]:
    """
    Retrieve a list of all tasks.

    Returns:
        A list of TaskRead objects representing all tasks.

    Raises:
        HTTPException: If the remote API call fails.
    """
    async with AsyncClient() as client:
        response = await client.get(base_url)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch tasks: {response.text}",
            )
        tasks_data = response.json()
        normalized = [_normalize_task(task) for task in tasks_data]
        return [TaskRead(**task) for task in normalized]


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    """
    Create a new task.

    Args:
        task: TaskCreate object containing task details.

    Returns:
        The created TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    payload = task.dict()
    payload["priority"] = task.priority.value.lower()
    payload["status"] = task.status.value.lower()

    async with AsyncClient() as client:
        response = await client.post(base_url, json=payload)
        if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create task: {response.text}",
            )
        task_data = response.json()
        normalized = _normalize_task(task_data)
        return TaskRead(**normalized)


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    """
    Retrieve a task by its ID.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The TaskRead object for the specified task.

    Raises:
        HTTPException: If the remote API call fails.
    """
    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch task {task_id}: {response.text}",
            )
        task_data = response.json()
        normalized = _normalize_task(task_data)
        return TaskRead(**normalized)


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    """
    Update an existing task.

    Args:
        task_id: The ID of the task to update.
        task: TaskUpdate object containing fields to update.

    Returns:
        The updated TaskRead object.

    Raises:
        HTTPException: If the remote API call fails.
    """
    payload = task.dict(exclude_unset=True)
    if "priority" in payload and payload["priority"] is not None:
        payload["priority"] = payload["priority"].value.lower()
    if "status" in payload and payload["status"] is not None:
        payload["status"] = payload["status"].value.lower()

    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.put(url, json=payload)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to update task {task_id}: {response.text}",
            )
        task_data = response.json()
        normalized = _normalize_task(task_data)
        return TaskRead(**normalized)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: The ID of the task to delete.

    Raises:
        HTTPException: If the remote API call fails.
    """
    url = f"{base_url}/{task_id}"
    async with AsyncClient() as client:
        response = await client.delete(url)
        if response.status_code != status.HTTP_204_NO_CONTENT:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to delete task {task_id}: {response.text}",
            )
    return None

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)