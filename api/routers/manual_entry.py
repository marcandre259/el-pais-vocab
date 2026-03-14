import asyncio
from fastapi import APIRouter

from api.config import settings
from api.schemas.manual_entry import ManualEntryRequest
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, llm

router = APIRouter(prefix="/manual", tags=["manual_entry"])


def _translate_manual_words(
    words: list[str],
    source_lang: str,
    target_lang: str,
    theme: str,
    progress_callback=None,
) -> dict:
    """Synchronous function to translate and store manual words."""
    # Get existing words in this theme to avoid duplicates
    known_words = db.get_known_words(theme=theme, db_path=settings.db_path)

    if progress_callback:
        progress_callback(f"Translating {len(words)} words...")

    # Translate words via LLM
    translated = llm.translate_words(
        words=words,
        source_lang=source_lang,
        target_lang=target_lang,
        theme_context=theme,
    )

    if progress_callback:
        progress_callback("Saving to database...")

    # Add words to vocabulary table
    new_count, updated_count = db.add_words(
        words=translated,
        source=None,
        source_lang=source_lang,
        target_lang=target_lang,
        theme=theme,
        db_path=settings.db_path,
    )

    return {
        "theme": theme,
        "new_words": new_count,
        "updated_words": updated_count,
    }


@router.post("/translate", response_model=TaskStatus)
async def translate_manual_words(request: ManualEntryRequest):
    """
    Translate a list of words and add them to a theme.

    Returns a task_id to poll for results.
    """
    task_id = task_manager.create_task(TaskType.MANUAL_ENTRY)

    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _translate_manual_words,
            request.words,
            request.source_lang,
            request.target_lang,
            request.theme,
        )
    )

    return task_manager.get_task(task_id)
