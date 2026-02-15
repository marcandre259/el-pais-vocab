import asyncio
from fastapi import APIRouter, HTTPException

from api.config import settings
from api.schemas.themes import (
    Theme,
    ThemeWithWords,
    ThemeCreateRequest,
)
from api.schemas.vocabulary import VocabularyWord
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, llm

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=list[Theme])
def list_themes():
    """List all registered themes."""
    themes = db.get_themes(settings.db_path)
    return [
        Theme(
            theme=t["theme"],
            source_lang=t["source_lang"],
            target_lang=t["target_lang"],
            created_at=str(t.get("created_at")) if t.get("created_at") else None,
            word_count=t.get("word_count", 0),
        )
        for t in themes
    ]


@router.get("/{theme_name}", response_model=ThemeWithWords)
def get_theme(theme_name: str):
    """Get a theme with all its vocabulary words."""
    words = db.get_all_words(settings.db_path, theme=theme_name)

    if not words:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Get theme metadata from get_themes
    themes = db.get_themes(settings.db_path)
    theme_info = next((t for t in themes if t["theme"] == theme_name), None)

    theme = Theme(
        theme=theme_name,
        source_lang=theme_info["source_lang"] if theme_info else words[0].get("source_lang", ""),
        target_lang=theme_info["target_lang"] if theme_info else words[0].get("target_lang", ""),
        created_at=str(theme_info.get("created_at")) if theme_info and theme_info.get("created_at") else None,
        word_count=theme_info.get("word_count", len(words)) if theme_info else len(words),
    )

    theme_words = [
        VocabularyWord(
            id=w["id"],
            word=w["word"],
            lemma=w["lemma"],
            pos=w.get("pos"),
            gender=w.get("gender"),
            translation=w["translation"],
            source_lang=w.get("source_lang"),
            target_lang=w.get("target_lang"),
            examples=w.get("examples", []) or [],
            source=w.get("source"),
            theme=w["theme"],
            added_at=str(w.get("added_at")) if w.get("added_at") else None,
        )
        for w in words
    ]

    return ThemeWithWords(theme=theme, words=theme_words)


def _create_theme_vocabulary(
    theme_prompt: str,
    source_lang: str,
    target_lang: str,
    word_count: int,
) -> dict:
    """Synchronous function to create themed vocabulary."""
    # Check for related existing theme
    existing_themes = db.get_themes(settings.db_path)
    related_theme = llm.detect_related_theme(
        theme_prompt, source_lang, target_lang, existing_themes
    )

    is_related = False
    related_theme_name = None

    if related_theme:
        target_theme = related_theme["theme"]
        is_related = True
        related_theme_name = related_theme["theme"]
        known_words = db.get_known_lemmas(theme=target_theme, db_path=settings.db_path)
    else:
        target_theme = theme_prompt
        known_words = []

    # Generate vocabulary using LLM with tool use
    words = llm.generate_themed_vocabulary(
        theme_prompt=theme_prompt,
        source_lang=source_lang,
        target_lang=target_lang,
        known_words=known_words,
        count=word_count,
        get_themes_func=lambda: db.get_themes(settings.db_path),
        search_words_func=lambda theme, st=None: db.search_words(
            theme, st, settings.db_path
        ),
    )

    # Add words to vocabulary table
    new_count, updated_count = db.add_words(
        words=words,
        source=None,
        source_lang=source_lang,
        target_lang=target_lang,
        theme=target_theme,
        db_path=settings.db_path,
    )

    return {
        "theme": target_theme,
        "new_words": new_count,
        "updated_words": updated_count,
        "is_related_theme": is_related,
        "related_theme_name": related_theme_name,
    }


@router.post("", response_model=TaskStatus)
async def create_theme(request: ThemeCreateRequest):
    """
    Create themed vocabulary using LLM generation.

    Returns a task_id to poll for results, as LLM generation takes 10-30 seconds.
    """
    task_id = task_manager.create_task(TaskType.THEME_CREATE)

    # Start background task
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _create_theme_vocabulary,
            request.theme_prompt,
            request.source_lang,
            request.target_lang,
            request.word_count,
        )
    )

    return task_manager.get_task(task_id)
