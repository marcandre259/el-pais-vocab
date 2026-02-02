from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ArticleExtractRequest(BaseModel):
    """Request model for article vocabulary extraction."""

    url: str = Field(..., description="URL of the El País article")
    browser: str = Field(
        default="firefox",
        description="Browser to extract cookies from (chrome, firefox, edge, opera)",
    )
    source_lang: str = Field(default="Spanish", description="Source language")
    target_lang: str = Field(default="French", description="Target language")
    word_count: int = Field(default=30, ge=1, le=100, description="Number of words to extract")
    prompt: str = Field(
        default="pick useful vocabulary words",
        description="Instructions for word selection",
    )


class ArticleExtractResult(BaseModel):
    """Result model for article vocabulary extraction."""

    new_words: int
    updated_words: int
    words: list[dict]
    source_url: str
