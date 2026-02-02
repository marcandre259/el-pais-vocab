from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from datetime import datetime


class TaskType(str, Enum):
    """Types of background tasks."""

    ARTICLE_EXTRACT = "article_extract"
    THEME_CREATE = "theme_create"
    AUDIO_GENERATE = "audio_generate"
    ANKI_SYNC = "anki_sync"


class TaskStatusEnum(str, Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(BaseModel):
    """Background task status model."""

    task_id: str
    type: TaskType
    status: TaskStatusEnum
    progress: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
