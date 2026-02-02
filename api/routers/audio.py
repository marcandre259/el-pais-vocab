import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.config import settings
from api.schemas.audio import AudioGenerateRequest, AudioGenerateResult
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, audio

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/{lemma}.mp3")
def get_audio(lemma: str):
    """Serve audio file for a lemma."""
    audio_path = settings.audio_path / f"{lemma}.mp3"

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"{lemma}.mp3",
    )


def _generate_all_audio(theme: str | None, language: str) -> dict:
    """Synchronous function to generate audio for all missing words."""
    if theme:
        # Get theme info for source language
        theme_info = db.get_theme_by_table_name(theme, settings.db_path)
        if theme_info:
            words = db.get_all_words_from_theme(theme, settings.db_path)
            lang = theme_info.get("source_lang", language)
        else:
            # Theme not found, try main vocabulary
            words = db.get_all_words(settings.db_path, theme=theme)
            lang = language
    else:
        # Main vocabulary (el_pais)
        words = db.get_all_words(settings.db_path)
        lang = language

    lemmas = [w["lemma"] for w in words]

    generated, skipped = audio.generate_all_audio(
        lemmas=lemmas,
        lang=lang,
        audio_dir=settings.audio_dir,
    )

    return {
        "generated": generated,
        "skipped": skipped,
        "total_lemmas": len(lemmas),
    }


@router.post("/generate", response_model=TaskStatus)
async def generate_audio(request: AudioGenerateRequest):
    """
    Generate audio for all missing vocabulary words.

    Returns a task_id to poll for results.
    """
    task_id = task_manager.create_task(TaskType.AUDIO_GENERATE)

    # Start background task
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _generate_all_audio,
            request.theme,
            request.language,
        )
    )

    return task_manager.get_task(task_id)
