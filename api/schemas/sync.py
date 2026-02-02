from typing import Optional
from pydantic import BaseModel, Field


class SyncStatus(BaseModel):
    """AnkiConnect connection status."""

    connected: bool
    message: str


class SyncRequest(BaseModel):
    """Request model for Anki sync."""

    include_main: bool = Field(
        default=True, description="Include main vocabulary table"
    )
    include_themes: bool = Field(default=True, description="Include themed vocabulary")
    theme_name: Optional[str] = Field(
        default=None, description="Sync only specific theme (by table_name)"
    )


class SyncResult(BaseModel):
    """Result model for Anki sync."""

    results: dict[str, dict[str, int]]
    total_added: int
    total_skipped: int
    total_failed: int
