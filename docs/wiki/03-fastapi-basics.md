# Chapter 3: FastAPI Basics

[← Previous: How Web Apps Work](02-how-web-apps-work.md) | [Back to Index](README.md) | [Next: Pydantic Data Validation →](04-pydantic-data-validation.md)

---

## What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It's known for:

- **Speed**: One of the fastest Python frameworks (on par with Node.js and Go)
- **Type hints**: Uses Python type hints for validation and documentation
- **Auto-documentation**: Generates interactive API docs automatically
- **Developer experience**: Great error messages and IDE support

---

## Your First Endpoint

Here's the simplest possible FastAPI application:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, World!"}
```

**What's happening:**
1. `FastAPI()` creates an application instance
2. `@app.get("/")` is a **decorator** that says "when someone makes a GET request to `/`, run this function"
3. The function returns a dictionary, which FastAPI automatically converts to JSON

---

## Real Example: The Health Check

From `api/app.py`:

```python
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "el-pais-vocab-api"}
```

**Why have a health check?**
- Load balancers use it to know if the server is alive
- Monitoring systems can ping it regularly
- It's a simple endpoint to test if the API is running

Try it: `curl http://localhost:8000/health`

---

## Path Parameters

Path parameters are parts of the URL that can vary:

From `api/routers/vocabulary.py`:

```python
@router.get("/{word_id}", response_model=VocabularyWord)
def get_word(word_id: int):
    """Get a single vocabulary word by ID."""
    # ... fetch word from database
```

**How it works:**
- `{word_id}` in the path means "capture this part of the URL"
- `word_id: int` in the function tells FastAPI to convert it to an integer
- Request to `/vocabulary/42` → `word_id` is `42`

**Automatic validation:**
- Request to `/vocabulary/abc` → 422 error (can't convert "abc" to int)
- No manual error handling needed!

---

## Query Parameters

Query parameters come after the `?` in a URL:

```
/vocabulary?page=2&page_size=10
```

From `api/routers/vocabulary.py`:

```python
from typing import Optional
from fastapi import Query

@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    theme: Optional[str] = Query(default=None),
):
    """List vocabulary words with pagination."""
    # page=1 by default, must be >= 1
    # page_size=50 by default, must be 1-100
    # theme is optional (can be None)
```

**Key points:**
- `Query()` lets you add constraints like `ge=1` (greater than or equal to 1)
- Default values make parameters optional
- `Optional[str]` means "string or None"

**Examples:**
```
GET /vocabulary              → page=1, page_size=50, theme=None
GET /vocabulary?page=2       → page=2, page_size=50, theme=None
GET /vocabulary?page_size=10 → page=1, page_size=10, theme=None
GET /vocabulary?page=0       → 422 error (page must be >= 1)
```

---

## Request Bodies

For `POST` requests, data comes in the request body:

From `api/routers/vocabulary.py`:

```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    theme: Optional[str] = None

@router.post("/search", response_model=SearchResult)
def search_vocabulary(request: SearchRequest):
    """Semantic search for vocabulary using LLM."""
    # request.query contains the search query
    # request.theme is optional
```

**How it works:**
1. Client sends JSON: `{"query": "words about food"}`
2. FastAPI validates it matches `SearchRequest` schema
3. Creates a `SearchRequest` object from the data
4. Passes it to your function

---

## Response Models

`response_model` tells FastAPI what the output looks like:

```python
@router.get("/stats", response_model=VocabularyStats)
def get_stats(theme: Optional[str] = Query(default=None)):
    """Get vocabulary statistics."""
    stats = db.get_stats(settings.db_path, theme=theme)
    return VocabularyStats(**stats)
```

**Benefits:**
- Documentation shows the exact response format
- FastAPI validates your return value
- Only includes fields defined in the model (no accidental data leaks)

---

## HTTP Status Codes and Exceptions

FastAPI provides `HTTPException` for error responses:

```python
from fastapi import HTTPException

@router.get("/{word_id}")
def get_word(word_id: int):
    # ... query database ...

    if not row:
        raise HTTPException(status_code=404, detail="Word not found")

    return VocabularyWord(...)
```

**What happens:**
1. Database returns no result
2. We raise `HTTPException` with status 404
3. FastAPI sends: `{"detail": "Word not found"}` with HTTP 404

**Common status codes:**
- `400` - Bad Request (client sent invalid data)
- `404` - Not Found (resource doesn't exist)
- `422` - Unprocessable Entity (validation failed)
- `500` - Server Error (something broke)

---

## The Request-Response Cycle

Let's trace a complete request through the vocabulary list endpoint:

```
1. Client Request
   GET /api/vocabulary?page=2&page_size=10

2. FastAPI Routing
   - Matches route: @router.get("")
   - Extracts query params: page=2, page_size=10, theme=None
   - Validates: 2 >= 1 ✓, 10 in 1-100 ✓

3. Function Execution
   def list_vocabulary(page: int, page_size: int, theme: Optional[str]):
       words = db.get_all_words(...)
       # Pagination logic
       return PaginatedResponse(items=..., total=...)

4. Response Serialization
   - PaginatedResponse → JSON
   - Status code 200

5. Client Response
   {
     "items": [...],
     "total": 100,
     "page": 2,
     "page_size": 10,
     "total_pages": 10
   }
```

---

## Application Structure

From `api/app.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import (
    vocabulary_router,
    articles_router,
    themes_router,
    # ...
)

# 1. Create the application
app = FastAPI(
    title="El País Vocabulary Builder API",
    description="REST API for extracting Spanish vocabulary...",
    version="1.0.0",
)

# 2. Add middleware (we'll cover this in Chapter 9)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # ...
)

# 3. Register routers (we'll cover this in Chapter 5)
app.include_router(vocabulary_router, prefix=settings.api_prefix)
app.include_router(articles_router, prefix=settings.api_prefix)
# ...

# 4. Define root-level endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Key points:**
- `FastAPI()` parameters become the API documentation
- Middleware wraps every request (for CORS, auth, logging, etc.)
- Routers organize endpoints by feature
- Prefix `/api` means all routes start with `/api/...`

---

## Automatic Documentation

FastAPI generates interactive documentation automatically:

**Swagger UI**: `http://localhost:8000/docs`
- Try out endpoints directly
- See request/response formats
- Auto-generated from your code

**ReDoc**: `http://localhost:8000/redoc`
- Alternative documentation format
- Better for reading/sharing

The documentation comes from:
- Function docstrings
- Type hints
- Pydantic models
- `Query()` and `Field()` descriptions

---

## Summary

| Concept | Example | Purpose |
|---------|---------|---------|
| **Decorator** | `@app.get("/path")` | Maps URL to function |
| **Path param** | `/{word_id}` | Variable part of URL |
| **Query param** | `?page=1` | Optional URL parameters |
| **Request body** | `request: SearchRequest` | JSON data in POST requests |
| **Response model** | `response_model=Word` | Define output format |
| **HTTPException** | `raise HTTPException(404, ...)` | Return error responses |

---

## Try It Yourself

1. Start the API: `uvicorn api.app:app --reload`
2. Visit `http://localhost:8000/docs`
3. Try the `/health` endpoint
4. Try `/api/vocabulary` with different query parameters
5. Look at the schema section to see the Pydantic models

---

## What's Next?

We briefly mentioned `SearchRequest` and `VocabularyWord` models. [Chapter 4: Pydantic Data Validation](04-pydantic-data-validation.md) explains how these work and why they're so powerful.

---

[← Previous: How Web Apps Work](02-how-web-apps-work.md) | [Back to Index](README.md) | [Next: Pydantic Data Validation →](04-pydantic-data-validation.md)
