import uuid
import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from api.schemas.tasks import TaskStatus, TaskType, TaskStatusEnum


class TaskManager:
    """In-memory background task manager."""

    def __init__(self, max_workers: int = 4):
        self._tasks: dict[str, TaskStatus] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def create_task(self, task_type: TaskType) -> str:
        """Create a new pending task and return its ID."""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskStatus(
            task_id=task_id,
            type=task_type,
            status=TaskStatusEnum.PENDING,
            created_at=datetime.now(),
        )
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status by ID."""
        return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatusEnum] = None,
        progress: Optional[str] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status."""
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        if status:
            # Create new TaskStatus with updated values (Pydantic models are immutable by default)
            self._tasks[task_id] = TaskStatus(
                task_id=task.task_id,
                type=task.type,
                status=status,
                progress=progress if progress is not None else task.progress,
                result=result if result is not None else task.result,
                error=error if error is not None else task.error,
                created_at=task.created_at,
                completed_at=datetime.now() if status in (TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED) else task.completed_at,
            )
        else:
            self._tasks[task_id] = TaskStatus(
                task_id=task.task_id,
                type=task.type,
                status=task.status,
                progress=progress if progress is not None else task.progress,
                result=result if result is not None else task.result,
                error=error if error is not None else task.error,
                created_at=task.created_at,
                completed_at=task.completed_at,
            )

    async def run_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> None:
        """Run a synchronous function in background thread pool."""
        self.update_task(task_id, status=TaskStatusEnum.IN_PROGRESS)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._executor, lambda: func(*args, **kwargs)
            )
            self.update_task(task_id, status=TaskStatusEnum.COMPLETED, result=result)
        except Exception as e:
            self.update_task(task_id, status=TaskStatusEnum.FAILED, error=str(e))

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Remove tasks older than max_age_hours. Returns count of removed tasks."""
        now = datetime.now()
        to_remove = []
        for task_id, task in self._tasks.items():
            age = now - task.created_at
            if age.total_seconds() > max_age_hours * 3600:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self._tasks[task_id]

        return len(to_remove)


# Global task manager instance
task_manager = TaskManager()
