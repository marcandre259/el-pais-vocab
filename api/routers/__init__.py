from .vocabulary import router as vocabulary_router
from .articles import router as articles_router
from .themes import router as themes_router
from .audio import router as audio_router
from .sync import router as sync_router
from .tasks import router as tasks_router

__all__ = [
    "vocabulary_router",
    "articles_router",
    "themes_router",
    "audio_router",
    "sync_router",
    "tasks_router",
]
