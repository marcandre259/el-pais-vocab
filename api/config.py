from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database
    db_path: str = "vocab.db"

    # Audio
    audio_dir: str = "audio"

    # API
    api_prefix: str = "/api"

    @property
    def audio_path(self) -> Path:
        return Path(self.audio_dir)

    @property
    def db_file(self) -> Path:
        return Path(self.db_path)

    class Config:
        env_prefix = "ELPAIS_"


settings = Settings()
