from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate, Priority, Status
from app.core.security import hash_password, verify_password
from app.core.config import Settings

settings = Settings()

PROJECT_NAME = "todo-app-test15"
TABLE_NAME = "tasks"

BASE_URL = f"{settings.db_api_url}/databases/{PROJECT_NAME}/data/{TABLE_NAME}"

app = FastAPI()


def _to_lowercase(value: str | None) -> str | None:
    return value.lower() if value is not None else None


def _to_uppercase(value: str | None) -> str | None:
    return value.upper() if value is not None else None


@app.get("/tasks", response_model=list[TaskRead])
async def list_tasks() -> list[TaskRead]:
    async with AsyncClient() as client:
        try:
            response = await client.get(BASE_URL)
            response.raise_for_status()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch tasks: {exc}",
            ) from exc

    tasks_data = response.json()
    for task in tasks_data:
        task["priority"] = _to_uppercase(task.get("priority"))
        task["status"] = _to_uppercase(task.get("status"))
    return tasks_data


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate) -> TaskRead:
    payload = task.dict()
    payload["priority"] = _to_lowercase(payload["priority"])
    payload["status"] = _to_lowercase(payload["status"])

    async with AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, json=payload)
            response.raise_for_status()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to create task: {exc}",
            ) from exc

    created_task = response.json()
    created_task["priority"] = _to_uppercase(created_task.get("priority"))
    created_task["status"] = _to_uppercase(created_task.get("status"))
    return created_task


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(task_id: int) -> TaskRead:
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found",
                )
            response.raise_for_status()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch task: {exc}",
            ) from exc

    task = response.json()
    task["priority"] = _to_uppercase(task.get("priority"))
    task["status"] = _to_uppercase(task.get("status"))
    return task


@app.put("/tasks/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, task: TaskUpdate) -> TaskRead:
    payload = task.dict(exclude_unset=True)
    if "priority" in payload:
        payload["priority"] = _to_lowercase(payload["priority"])
    if "status" in payload:
        payload["status"] = _to_lowercase(payload["status"])

    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        try:
            response = await client.put(url, json=payload)
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found",
                )
            response.raise_for_status()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to update task: {exc}",
            ) from exc

    updated_task = response.json()
    updated_task["priority"] = _to_uppercase(updated_task.get("priority"))
    updated_task["status"] = _to_uppercase(updated_task.get("status"))
    return updated_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int) -> None:
    url = f"{BASE_URL}/{task_id}"
    async with AsyncClient() as client:
        try:
            response = await client.delete(url)
            if response.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found",
                )
            response.raise_for_status()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to delete task: {exc}",
            ) from exc
    return
