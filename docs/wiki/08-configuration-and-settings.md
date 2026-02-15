# Chapter 8: Configuration and Settings

[← Previous: Background Tasks](07-background-tasks.md) | [Back to Index](README.md) | [Next: Middleware and CORS →](09-middleware-and-cors.md)

---

## Why Configuration Matters

Hardcoding values leads to problems:

```python
# BAD: Hardcoded values
conn = sqlite3.connect("/home/user/prod.db")  # What about dev? testing?
origins = ["http://production.com"]           # Can't test locally
```

**Configuration lets you:**
- Use different databases for dev/test/prod
- Change behavior without code changes
- Keep secrets out of source code

---

## Environment Variables

Environment variables are the standard way to configure applications:

```bash
# Set in shell
export DATABASE_PATH=/path/to/db.sqlite
export API_KEY=secret123

# Or in .env file
DATABASE_PATH=/path/to/db.sqlite
API_KEY=secret123
```

**Access in Python:**

```python
import os

db_path = os.getenv("DATABASE_PATH", "default.db")
api_key = os.getenv("API_KEY")  # None if not set
```

---

## Pydantic Settings

Pydantic Settings provides type-safe configuration with automatic environment variable loading.

From `api/config.py`:

```python
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
```

**Key features:**

1. **Type hints with defaults**
   ```python
   db_path: str = "vocab.db"  # Default value if not in env
   cors_origins: list[str] = [...]  # Even complex types work
   ```

2. **Environment variable prefix**
   ```python
   class Config:
       env_prefix = "ELPAIS_"
   ```
   This means the setting `db_path` reads from `ELPAIS_DB_PATH`.

3. **Properties for computed values**
   ```python
   @property
   def audio_path(self) -> Path:
       return Path(self.audio_dir)
   ```

---

## How Environment Variables Map

With `env_prefix = "ELPAIS_"`:

| Setting | Environment Variable |
|---------|---------------------|
| `db_path` | `ELPAIS_DB_PATH` |
| `audio_dir` | `ELPAIS_AUDIO_DIR` |
| `api_prefix` | `ELPAIS_API_PREFIX` |
| `cors_origins` | `ELPAIS_CORS_ORIGINS` |

**Example .env file:**

```bash
ELPAIS_DB_PATH=/data/production.db
ELPAIS_AUDIO_DIR=/data/audio
ELPAIS_CORS_ORIGINS=["https://myapp.com", "https://api.myapp.com"]
```

---

## Singleton Pattern

The settings object is created once and imported everywhere:

```python
# In config.py
settings = Settings()  # Created once

# In any other file
from api.config import settings

def some_function():
    db = sqlite3.connect(settings.db_path)
```

**Benefits:**
- Configuration loaded once at startup
- Same settings everywhere
- Easy to mock in tests

---

## Using Settings in Routes

From `api/routers/vocabulary.py`:

```python
from api.config import settings

@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(...):
    words = db.get_all_words(settings.db_path, theme=theme)
    # ...
```

From `api/app.py`:

```python
from api.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # From config
    # ...
)

app.include_router(vocabulary_router, prefix=settings.api_prefix)
```

---

## Default Values Strategy

Choose defaults for development, override for production:

```python
class Settings(BaseSettings):
    # Good for local development
    db_path: str = "vocab.db"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Require explicit setting (no default)
    api_key: str  # Will error if ELPAIS_API_KEY not set
```

**In production:**

```bash
export ELPAIS_DB_PATH=/var/data/prod.db
export ELPAIS_CORS_ORIGINS='["https://myapp.com"]'
export ELPAIS_API_KEY=secret123
```

---

## Properties for Computed Values

Properties let you derive values from settings:

```python
class Settings(BaseSettings):
    audio_dir: str = "audio"

    @property
    def audio_path(self) -> Path:
        """Convert string to Path object."""
        return Path(self.audio_dir)

    @property
    def audio_cache_path(self) -> Path:
        """Derived path for cache."""
        return self.audio_path / "cache"
```

**Usage:**

```python
from api.config import settings

# String setting
print(settings.audio_dir)  # "audio"

# Computed property
print(settings.audio_path)  # Path("audio")
print(settings.audio_cache_path)  # Path("audio/cache")
```

---

## Loading from .env Files

Pydantic Settings can load from `.env` files:

```python
class Settings(BaseSettings):
    db_path: str = "vocab.db"

    class Config:
        env_prefix = "ELPAIS_"
        env_file = ".env"  # Load from .env file
```

**.env file:**

```bash
ELPAIS_DB_PATH=production.db
ELPAIS_AUDIO_DIR=/data/audio
```

**Priority (highest to lowest):**
1. Actual environment variables
2. `.env` file values
3. Default values in code

---

## Type Coercion

Pydantic Settings automatically converts types:

```python
class Settings(BaseSettings):
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = []
```

**Environment variables are strings, but Pydantic converts:**

```bash
export ELPAIS_PORT=3000        # Becomes int 3000
export ELPAIS_DEBUG=true       # Becomes bool True
export ELPAIS_CORS_ORIGINS='["http://a.com", "http://b.com"]'  # Becomes list
```

---

## Validation

Settings are validated at startup:

```python
class Settings(BaseSettings):
    port: int = Field(ge=1, le=65535)
    log_level: str = Field(pattern="^(DEBUG|INFO|WARNING|ERROR)$")
```

**If validation fails, the app won't start:**

```bash
export ELPAIS_PORT=99999  # Invalid
# pydantic.error_wrappers.ValidationError:
# port: ensure this value is less than or equal to 65535
```

---

## Testing with Different Settings

Override settings in tests:

```python
import pytest
from api.config import Settings

@pytest.fixture
def test_settings():
    return Settings(
        db_path=":memory:",  # SQLite in-memory
        audio_dir="/tmp/test_audio",
    )

def test_something(test_settings, monkeypatch):
    # Replace the global settings
    monkeypatch.setattr("api.config.settings", test_settings)
    # Now all code using settings.db_path gets ":memory:"
```

---

## Complete Example

Here's how configuration flows through the app:

```
1. Environment / .env file
   ELPAIS_DB_PATH=/data/vocab.db

2. Settings class loads it
   class Settings(BaseSettings):
       db_path: str = "vocab.db"
       class Config:
           env_prefix = "ELPAIS_"

3. Singleton created
   settings = Settings()
   # settings.db_path == "/data/vocab.db"

4. Used throughout app
   from api.config import settings

   @router.get("")
   def list_words():
       words = db.get_all_words(settings.db_path)
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| **BaseSettings** | Type-safe configuration class |
| **env_prefix** | Namespace for env variables |
| **Default values** | Fallback when not configured |
| **Properties** | Computed/derived settings |
| **Singleton** | One settings instance for app |
| **.env file** | Store config outside code |

---

## Try It Yourself

1. Look at `api/config.py`
2. Set an environment variable:
   ```bash
   export ELPAIS_DB_PATH=test.db
   ```
3. Start the API and verify it uses the new path
4. Try adding a new setting and using it in a route

---

## What's Next?

You've seen `settings.cors_origins` used in the app setup. [Chapter 9: Middleware and CORS](09-middleware-and-cors.md) explains what CORS is and why middleware matters.

---

[← Previous: Background Tasks](07-background-tasks.md) | [Back to Index](README.md) | [Next: Middleware and CORS →](09-middleware-and-cors.md)
