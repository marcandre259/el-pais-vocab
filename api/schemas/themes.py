from typing import Optional
from pydantic import BaseModel, Field
from api.schemas.vocabulary import VocabularyWord


class Theme(BaseModel):
    """Theme metadata model."""

    theme: str
    source_lang: str
    target_lang: str
    created_at: Optional[str] = None
    word_count: int = 0

    class Config:
        from_attributes = True


class ThemeWithWords(BaseModel):
    """Theme with its vocabulary words."""

    theme: Theme
    words: list[VocabularyWord]


class ThemeCreateRequest(BaseModel):
    """Request model for creating themed vocabulary."""

    theme_prompt: str = Field(..., min_length=1, description="Theme description")
    source_lang: str = Field(default="Dutch", description="Source language")
    target_lang: str = Field(default="English", description="Target language")
    word_count: int = Field(default=20, ge=1, le=100, description="Number of words to generate")


class ThemeCreateResult(BaseModel):
    """Result model for theme creation."""

    theme: str
    new_words: int
    updated_words: int
    is_related_theme: bool = False
    related_theme_name: Optional[str] = None
