import asyncio
from fastapi import APIRouter, BackgroundTasks

from api.config import settings
from api.schemas.articles import ArticleExtractRequest, ArticleExtractResult
from api.schemas.tasks import TaskStatus, TaskType
from api.services.task_manager import task_manager

from core import db, llm, scraper

router = APIRouter(prefix="/articles", tags=["articles"])


def _extract_article_vocabulary(
    url: str,
    browser: str,
    source_lang: str,
    target_lang: str,
    word_count: int,
    prompt: str,
) -> dict:
    """Synchronous function to extract vocabulary from article."""
    # Fetch article text
    article_text = scraper.get_article_text(url, browser)

    # Get known words to exclude
    known_words = db.get_known_lemmas("el_pais", settings.db_path)

    # Extract vocabulary using LLM
    words = llm.select_and_translate(
        article_text=article_text,
        known_words=known_words,
        target_lang=target_lang,
        source_lang=source_lang,
        user_prompt=prompt,
        count=word_count,
    )

    if not words:
        return {
            "new_words": 0,
            "updated_words": 0,
            "words": [],
            "source_url": url,
        }

    # Add words to database
    new_count, updated_count = db.add_words(
        words=words,
        source=url,
        source_lang=source_lang,
        target_lang=target_lang,
        theme="el_pais",
        db_path=settings.db_path,
    )

    return {
        "new_words": new_count,
        "updated_words": updated_count,
        "words": words,
        "source_url": url,
    }


@router.post("/extract", response_model=TaskStatus)
async def extract_vocabulary(request: ArticleExtractRequest):
    """
    Extract vocabulary from an El País article.

    Returns a task_id to poll for results, as LLM extraction takes 10-30 seconds.
    """
    task_id = task_manager.create_task(TaskType.ARTICLE_EXTRACT)

    # Start background task
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _extract_article_vocabulary,
            request.url,
            request.browser,
            request.source_lang,
            request.target_lang,
            request.word_count,
            request.prompt,
        )
    )

    return task_manager.get_task(task_id)
