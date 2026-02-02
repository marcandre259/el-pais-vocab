from typing import Optional
from pydantic import BaseModel, Field


class Theme(BaseModel):
    """Theme metadata model."""

    id: int
    table_name: str
    theme_description: str
    source_lang: str
    target_lang: str
    deck_name: str
    created_at: Optional[str] = None
    word_count: int = 0

    class Config:
        from_attributes = True


class ThemeWord(BaseModel):
    """Word from a theme table."""

    id: int
    word: str
    lemma: str
    pos: Optional[str] = None
    translation: str
    examples: list[str] = Field(default_factory=list)
    added_at: Optional[str] = None


class ThemeWithWords(BaseModel):
    """Theme with its vocabulary words."""

    theme: Theme
    words: list[ThemeWord]


class ThemeCreateRequest(BaseModel):
    """Request model for creating themed vocabulary."""

    theme_prompt: str = Field(..., min_length=1, description="Theme description")
    source_lang: str = Field(default="Dutch", description="Source language")
    target_lang: str = Field(default="English", description="Target language")
    word_count: int = Field(default=20, ge=1, le=100, description="Number of words to generate")
    deck_name: Optional[str] = Field(
        default=None, description="Anki deck name (defaults to theme name)"
    )


class ThemeCreateResult(BaseModel):
    """Result model for theme creation."""

    table_name: str
    theme_description: str
    new_words: int
    updated_words: int
    is_related_theme: bool = False
    related_theme_name: Optional[str] = None
