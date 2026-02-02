from typing import Optional
from pydantic import BaseModel, Field


class AudioGenerateRequest(BaseModel):
    """Request model for audio generation."""

    theme: Optional[str] = Field(
        default=None,
        description="Theme to generate audio for (None for main vocabulary)",
    )
    language: str = Field(
        default="Spanish",
        description="Language for TTS (e.g., Spanish, Dutch, French)",
    )


class AudioGenerateResult(BaseModel):
    """Result model for audio generation."""

    generated: int
    skipped: int
    total_lemmas: int
