from pydantic import BaseModel, Field


class ManualEntryRequest(BaseModel):
    """Request model for manual word translation."""

    words: list[str] = Field(..., min_length=1, description="List of words to translate")
    source_lang: str = Field(default="Dutch", description="Source language")
    target_lang: str = Field(default="English", description="Target language")
    theme: str = Field(..., min_length=1, description="Theme name for the words")
