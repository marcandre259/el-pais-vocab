import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.config import settings
from api.schemas.vocabulary import (
    VocabularyWord,
    VocabularyStats,
    PaginatedResponse,
    SearchRequest,
    SearchResult,
)

from core import db, llm

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    theme: Optional[str] = Query(default=None),
):
    """List vocabulary words with pagination."""
    words = db.get_all_words(settings.db_path, theme=theme)

    # Calculate pagination
    total = len(words)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    paginated_words = words[start:end]

    # Convert to response models
    items = [
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
        for w in paginated_words
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=VocabularyStats)
def get_stats(theme: Optional[str] = Query(default=None)):
    """Get vocabulary statistics."""
    stats = db.get_stats(settings.db_path, theme=theme)
    return VocabularyStats(**stats)


@router.get("/{word_id}", response_model=VocabularyWord)
def get_word(word_id: int):
    """Get a single vocabulary word by ID."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang,
               examples, source, theme, added_at
        FROM vocabulary
        WHERE id = ?
    """,
        (word_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Word not found")

    word_dict = dict(row)
    if word_dict["examples"]:
        import json
        word_dict["examples"] = json.loads(word_dict["examples"])
    else:
        word_dict["examples"] = []

    return VocabularyWord(
        id=word_dict["id"],
        word=word_dict["word"],
        lemma=word_dict["lemma"],
        pos=word_dict.get("pos"),
        gender=word_dict.get("gender"),
        translation=word_dict["translation"],
        source_lang=word_dict.get("source_lang"),
        target_lang=word_dict.get("target_lang"),
        examples=word_dict.get("examples", []),
        source=word_dict.get("source"),
        theme=word_dict["theme"],
        added_at=str(word_dict.get("added_at")) if word_dict.get("added_at") else None,
    )


@router.delete("/{word_id}")
def delete_word(word_id: int):
    """Delete a vocabulary word by ID."""
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vocabulary WHERE id = ?", (word_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Word not found")

    cursor.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()

    return {"message": "Word deleted successfully"}


@router.post("/search", response_model=SearchResult)
def search_vocabulary(request: SearchRequest):
    """Semantic search for vocabulary using LLM."""
    words = db.get_all_words(settings.db_path, theme=request.theme)

    if not words:
        raise HTTPException(status_code=404, detail="No words found to search")

    try:
        selected_word = llm.pick_word_by_prompt(words, request.query)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    word_response = VocabularyWord(
        id=selected_word["id"],
        word=selected_word["word"],
        lemma=selected_word["lemma"],
        pos=selected_word.get("pos"),
        gender=selected_word.get("gender"),
        translation=selected_word["translation"],
        source_lang=selected_word.get("source_lang"),
        target_lang=selected_word.get("target_lang"),
        examples=selected_word.get("examples", []) or [],
        source=selected_word.get("source"),
        theme=selected_word["theme"],
        added_at=str(selected_word.get("added_at")) if selected_word.get("added_at") else None,
    )

    return SearchResult(word=word_response)
