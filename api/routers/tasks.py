from fastapi import APIRouter, HTTPException

from api.schemas.tasks import TaskStatus
from api.services.task_manager import task_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """Get the status of a background task."""
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
