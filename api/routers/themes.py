import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException

from api.config import settings
from api.schemas.themes import (
    Theme,
    ThemeWord,
    ThemeWithWords,
    ThemeCreateRequest,
    ThemeCreateResult,
)
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, llm

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=list[Theme])
def list_themes():
    """List all registered themes."""
    themes = db.get_all_themes(settings.db_path)
    return [
        Theme(
            id=t["id"],
            table_name=t["table_name"],
            theme_description=t["theme_description"],
            source_lang=t["source_lang"],
            target_lang=t["target_lang"],
            deck_name=t["deck_name"],
            created_at=str(t.get("created_at")) if t.get("created_at") else None,
            word_count=t.get("word_count", 0),
        )
        for t in themes
    ]


@router.get("/{table_name}", response_model=ThemeWithWords)
def get_theme(table_name: str):
    """Get a theme with all its vocabulary words."""
    theme_info = db.get_theme_by_table_name(table_name, settings.db_path)
    if not theme_info:
        raise HTTPException(status_code=404, detail="Theme not found")

    words = db.get_all_words_from_theme(table_name, settings.db_path)

    theme = Theme(
        id=theme_info["id"],
        table_name=theme_info["table_name"],
        theme_description=theme_info["theme_description"],
        source_lang=theme_info["source_lang"],
        target_lang=theme_info["target_lang"],
        deck_name=theme_info["deck_name"],
        created_at=str(theme_info.get("created_at")) if theme_info.get("created_at") else None,
        word_count=theme_info.get("word_count", 0),
    )

    theme_words = [
        ThemeWord(
            id=w["id"],
            word=w["word"],
            lemma=w["lemma"],
            pos=w.get("pos"),
            translation=w["translation"],
            examples=w.get("examples", []) or [],
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
    deck_name: Optional[str],
) -> dict:
    """Synchronous function to create themed vocabulary."""
    # Check for related existing theme
    existing_themes = db.get_all_themes(settings.db_path)
    related_theme = llm.detect_related_theme(
        theme_prompt, source_lang, target_lang, existing_themes
    )

    is_related = False
    related_theme_name = None

    if related_theme:
        # Add to existing theme
        table_name = related_theme["table_name"]
        is_related = True
        related_theme_name = related_theme["theme_description"]
        known_words = db.get_known_lemmas_from_theme(table_name, settings.db_path)
    else:
        # Create new theme
        table_name = db.sanitize_table_name(theme_prompt)
        actual_deck_name = deck_name or theme_prompt.title().replace(" ", "-")
        db.create_theme_table(
            table_name=table_name,
            theme_description=theme_prompt,
            source_lang=source_lang,
            target_lang=target_lang,
            deck_name=actual_deck_name,
            db_path=settings.db_path,
        )
        known_words = []

    # Generate vocabulary using LLM with tool use
    words = llm.generate_themed_vocabulary(
        theme_prompt=theme_prompt,
        source_lang=source_lang,
        target_lang=target_lang,
        known_words=known_words,
        count=word_count,
        get_all_themes_func=lambda: db.get_all_themes(settings.db_path),
        search_theme_words_func=lambda tn, st=None: db.search_theme_words(
            tn, st, settings.db_path
        ),
    )

    # Add words to theme table
    new_count, updated_count = db.add_words_to_theme(
        words=words, table_name=table_name, db_path=settings.db_path
    )

    return {
        "table_name": table_name,
        "theme_description": theme_prompt,
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
            request.deck_name,
        )
    )

    return task_manager.get_task(task_id)
