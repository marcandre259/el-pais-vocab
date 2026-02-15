# Chapter 5: Routers and Organization

[← Previous: Pydantic Data Validation](04-pydantic-data-validation.md) | [Back to Index](README.md) | [Next: CRUD Operations →](06-crud-operations.md)

---

## Why Split Code Into Routers?

Imagine putting every endpoint in one file:

```python
# app.py - 2000 lines of endpoints
@app.get("/vocabulary")
@app.get("/vocabulary/{id}")
@app.post("/vocabulary")
@app.delete("/vocabulary/{id}")
@app.get("/articles")
@app.post("/articles/extract")
@app.get("/themes")
@app.post("/themes")
@app.get("/audio/{word}")
# ... and dozens more
```

Problems:
- Hard to find anything
- Merge conflicts when multiple people edit
- No clear ownership or boundaries
- Testing becomes difficult

**Solution:** Routers - logical groupings of related endpoints.

---

## What is a Router?

A router is a mini-application that handles a group of related endpoints:

```python
from fastapi import APIRouter

# Create a router
router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])

# Add endpoints to it
@router.get("")
def list_words():
    ...

@router.get("/{word_id}")
def get_word(word_id: int):
    ...
```

Think of it like a folder for endpoints.

---

## Creating a Router

From `api/routers/vocabulary.py`:

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.config import settings
from api.schemas.vocabulary import (
    VocabularyWord,
    VocabularyStats,
    PaginatedResponse,
)
from core import db

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    theme: Optional[str] = Query(default=None),
):
    """List vocabulary words with pagination."""
    # Implementation...


@router.get("/stats", response_model=VocabularyStats)
def get_stats(theme: Optional[str] = Query(default=None)):
    """Get vocabulary statistics."""
    # Implementation...


@router.get("/{word_id}", response_model=VocabularyWord)
def get_word(word_id: int):
    """Get a single vocabulary word by ID."""
    # Implementation...
```

**Key parts:**

| Part | Purpose |
|------|---------|
| `prefix="/vocabulary"` | All routes start with `/vocabulary` |
| `tags=["vocabulary"]` | Groups endpoints in API docs |
| `@router.get("")` | Handles GET `/vocabulary` |
| `@router.get("/{word_id}")` | Handles GET `/vocabulary/123` |

---

## Registering Routers with the App

From `api/routers/__init__.py`:

```python
from .vocabulary import router as vocabulary_router
from .articles import router as articles_router
from .themes import router as themes_router
from .audio import router as audio_router
from .sync import router as sync_router
from .tasks import router as tasks_router

__all__ = [
    "vocabulary_router",
    "articles_router",
    "themes_router",
    "audio_router",
    "sync_router",
    "tasks_router",
]
```

From `api/app.py`:

```python
from api.routers import (
    vocabulary_router,
    articles_router,
    themes_router,
    audio_router,
    sync_router,
    tasks_router,
)

app = FastAPI(...)

# Register each router with the app
app.include_router(vocabulary_router, prefix=settings.api_prefix)
app.include_router(articles_router, prefix=settings.api_prefix)
app.include_router(themes_router, prefix=settings.api_prefix)
app.include_router(audio_router, prefix=settings.api_prefix)
app.include_router(sync_router, prefix=settings.api_prefix)
app.include_router(tasks_router, prefix=settings.api_prefix)
```

**How prefixes work:**

```
Router prefix:  /vocabulary
App prefix:     /api
Final path:     /api/vocabulary

For @router.get("/{word_id}"):
Final path:     /api/vocabulary/123
```

---

## Our Router Structure

```
api/routers/
├── __init__.py       # Export all routers
├── vocabulary.py     # Word CRUD operations
├── articles.py       # Article extraction
├── themes.py         # Theme management
├── audio.py          # Audio file generation
├── sync.py           # Anki synchronization
└── tasks.py          # Background task status
```

**The pattern: one router per feature/resource**

| Router | Responsibility | Example Endpoints |
|--------|---------------|-------------------|
| `vocabulary` | Word management | List, get, delete words |
| `articles` | Article processing | Extract vocabulary from URL |
| `themes` | Theme management | List themes, create themed vocab |
| `audio` | Audio files | Get/generate pronunciation |
| `sync` | Anki integration | Sync words to Anki |
| `tasks` | Task status | Poll background task progress |

---

## Router File Anatomy

Every router file follows this structure:

```python
# 1. Imports
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.config import settings
from api.schemas.xxx import SomeModel
from core import some_module

# 2. Create router
router = APIRouter(prefix="/resource", tags=["resource"])

# 3. Define endpoints
@router.get("")
def list_items():
    """Docstring becomes API documentation."""
    ...

@router.get("/{item_id}")
def get_item(item_id: int):
    ...

@router.post("")
def create_item(request: CreateRequest):
    ...

@router.delete("/{item_id}")
def delete_item(item_id: int):
    ...
```

---

## Tags and Documentation

The `tags` parameter organizes the Swagger UI:

```python
router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])
```

In the docs (`/docs`), endpoints are grouped by tag:

```
▼ vocabulary
  GET  /api/vocabulary         List vocabulary words
  GET  /api/vocabulary/stats   Get vocabulary statistics
  GET  /api/vocabulary/{id}    Get a single word
  DELETE /api/vocabulary/{id}  Delete a word

▼ articles
  POST /api/articles/extract   Extract vocabulary from article

▼ themes
  GET  /api/themes             List themes
  POST /api/themes             Create themed vocabulary
```

---

## Benefits of Router Organization

### 1. Clear Boundaries

Each router has a single responsibility:
- `vocabulary.py` only deals with words
- `articles.py` only deals with article extraction
- Changes to one feature don't affect others

### 2. Easier Testing

You can test routers in isolation:

```python
from fastapi.testclient import TestClient
from api.routers.vocabulary import router

# Test just the vocabulary router
client = TestClient(router)
response = client.get("")
```

### 3. Team Collaboration

Multiple developers can work on different routers without conflicts.

### 4. Consistent URLs

The prefix ensures all related endpoints share a base path:
- `/api/vocabulary`
- `/api/vocabulary/stats`
- `/api/vocabulary/123`

---

## Advanced: Router Dependencies

You can add dependencies that apply to all endpoints in a router:

```python
from fastapi import Depends

def get_current_user():
    # Authentication logic
    ...

# All endpoints in this router require authentication
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user)]
)
```

---

## Common Patterns

### Helper Functions in Routers

From `api/routers/articles.py`:

```python
# Private helper function (not an endpoint)
def _extract_article_vocabulary(url: str, ...) -> dict:
    """Synchronous function to extract vocabulary from article."""
    article_text = scraper.get_article_text(url, browser)
    # ... processing logic
    return result

# Public endpoint that uses the helper
@router.post("/extract", response_model=TaskStatus)
async def extract_vocabulary(request: ArticleExtractRequest):
    task_id = task_manager.create_task(TaskType.ARTICLE_EXTRACT)
    asyncio.create_task(
        task_manager.run_task(task_id, _extract_article_vocabulary, ...)
    )
    return task_manager.get_task(task_id)
```

**Convention:** Prefix helper functions with `_` to indicate they're private.

### Importing Shared Logic

Routers call into `core/` modules for business logic:

```python
from core import db, llm, scraper

@router.get("")
def list_vocabulary(...):
    words = db.get_all_words(settings.db_path)  # Core module handles DB
    # Router handles HTTP concerns
```

This keeps routers thin - they translate HTTP to business logic.

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Router** | Groups related endpoints |
| **prefix** | Base URL for all endpoints |
| **tags** | Groups in API docs |
| **include_router** | Attaches router to app |
| **One router per feature** | Clear organization |

---

## Our File Structure

```
api/
├── app.py              # Main app, middleware, router registration
├── config.py           # Settings
├── routers/            # Endpoint handlers
│   ├── __init__.py     # Export routers
│   ├── vocabulary.py   # /api/vocabulary/*
│   ├── articles.py     # /api/articles/*
│   ├── themes.py       # /api/themes/*
│   ├── audio.py        # /api/audio/*
│   ├── sync.py         # /api/sync/*
│   └── tasks.py        # /api/tasks/*
├── schemas/            # Pydantic models
│   ├── vocabulary.py
│   ├── articles.py
│   ├── themes.py
│   └── tasks.py
└── services/           # Business logic services
    └── task_manager.py
```

---

## Try It Yourself

1. Open `http://localhost:8000/docs`
2. Notice how endpoints are grouped by tags
3. Look at `api/routers/vocabulary.py` and trace how the prefix works
4. Create a new router file and register it (just for practice)

---

## What's Next?

Now that you understand how code is organized, [Chapter 6: CRUD Operations](06-crud-operations.md) dives into the specific patterns for Create, Read, Update, and Delete endpoints.

---

[← Previous: Pydantic Data Validation](04-pydantic-data-validation.md) | [Back to Index](README.md) | [Next: CRUD Operations →](06-crud-operations.md)
