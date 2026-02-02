from datetime import datetime
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class VocabularyWord(BaseModel):
    """Vocabulary word response model."""

    id: int
    word: str
    lemma: str
    pos: Optional[str] = None
    gender: Optional[str] = None
    translation: str
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    examples: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    theme: str
    added_at: Optional[str] = None

    class Config:
        from_attributes = True


class VocabularyWordCreate(BaseModel):
    """Model for creating a vocabulary word."""

    word: str
    lemma: str
    pos: Optional[str] = None
    gender: Optional[str] = None
    translation: str
    source_lang: str = "Spanish"
    target_lang: str = "French"
    examples: list[str] = Field(default_factory=list)
    source: Optional[str] = None
    theme: str = "el_pais"


class VocabularyStats(BaseModel):
    """Vocabulary statistics response model."""

    total_words: int
    by_pos: dict[str, int]
    by_theme: dict[str, int]


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchRequest(BaseModel):
    """Semantic search request model."""

    query: str = Field(..., min_length=1, description="Search query")
    theme: Optional[str] = None


class SearchResult(BaseModel):
    """Semantic search result model."""

    word: VocabularyWord
    relevance_explanation: Optional[str] = None
