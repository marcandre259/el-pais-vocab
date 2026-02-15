import asyncio
from fastapi import APIRouter, HTTPException

from api.config import settings
from api.schemas.sync import SyncStatus, SyncRequest, SyncResult
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, anki_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatus)
def check_anki_status():
    """Check if AnkiConnect is accessible."""
    connected = anki_sync.check_connection()

    if connected:
        return SyncStatus(connected=True, message="AnkiConnect is running")
    else:
        return SyncStatus(
            connected=False,
            message="Cannot connect to AnkiConnect. Ensure Anki is running with AnkiConnect addon installed.",
        )


def _sync_to_anki(
    include_main: bool,
    include_themes: bool,
    theme_name: str | None,
) -> dict:
    """Synchronous function to sync vocabulary to Anki."""
    # Check connection first
    if not anki_sync.check_connection():
        raise ConnectionError(
            "Cannot connect to AnkiConnect. "
            "Ensure Anki is running with AnkiConnect addon installed."
        )

    results = {}
    total_added = 0
    total_skipped = 0
    total_failed = 0

    # Sync specific theme only
    if theme_name:
        # Verify theme exists
        themes = db.get_themes(settings.db_path)
        theme_exists = any(t['theme'] == theme_name for t in themes)
        if not theme_exists and theme_name != "el_pais":
            raise ValueError(f"Theme not found: {theme_name}")

        # Derive deck name
        words_in_name = theme_name.split()
        significant = [w for w in words_in_name if len(w) > 3][:3]
        deck_name = (
            "-".join(w.capitalize() for w in significant) if significant else theme_name
        )

        stats = anki_sync.sync_to_anki(
            db_path=settings.db_path,
            audio_dir=settings.audio_dir,
            deck_name=deck_name,
            theme=theme_name,
        )
        results[deck_name] = stats
        total_added = stats["added"]
        total_skipped = stats["skipped"]
        total_failed = stats["failed"]
    else:
        # Sync main vocabulary
        if include_main:
            stats = anki_sync.sync_to_anki(
                db_path=settings.db_path,
                audio_dir=settings.audio_dir,
                deck_name="el-pais",
                theme="el_pais",
            )
            results["el-pais"] = stats
            total_added += stats["added"]
            total_skipped += stats["skipped"]
            total_failed += stats["failed"]

        # Sync all themes
        if include_themes:
            themes = db.get_themes(settings.db_path)
            for t in themes:
                theme = t["theme"]
                words_in_name = theme.split()
                significant = [w for w in words_in_name if len(w) > 3][:3]
                deck_name = (
                    "-".join(w.capitalize() for w in significant) if significant else theme
                )

                stats = anki_sync.sync_to_anki(
                    db_path=settings.db_path,
                    audio_dir=settings.audio_dir,
                    deck_name=deck_name,
                    theme=theme,
                )
                results[deck_name] = stats
                total_added += stats["added"]
                total_skipped += stats["skipped"]
                total_failed += stats["failed"]

    return {
        "results": results,
        "total_added": total_added,
        "total_skipped": total_skipped,
        "total_failed": total_failed,
    }


@router.post("/anki", response_model=TaskStatus)
async def sync_anki(request: SyncRequest):
    """
    Sync vocabulary to Anki.

    Returns a task_id to poll for results.
    """
    task_id = task_manager.create_task(TaskType.ANKI_SYNC)

    # Start background task
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _sync_to_anki,
            request.include_main,
            request.include_themes,
            request.theme_name,
        )
    )

    return task_manager.get_task(task_id)
