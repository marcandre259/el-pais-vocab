# Chapter 6: CRUD Operations

[← Previous: Routers and Organization](05-routers-and-organization.md) | [Back to Index](README.md) | [Next: Background Tasks →](07-background-tasks.md)

---

## What is CRUD?

CRUD stands for the four basic database operations:

| Operation | HTTP Method | SQL | Example |
|-----------|-------------|-----|---------|
| **C**reate | POST | INSERT | Add a new word |
| **R**ead | GET | SELECT | List words, get one word |
| **U**pdate | PUT/PATCH | UPDATE | Change a translation |
| **D**elete | DELETE | DELETE | Remove a word |

Most APIs are built around these operations on resources.

---

## Read Operations

### Listing Resources (GET collection)

From `api/routers/vocabulary.py`:

```python
@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    theme: Optional[str] = Query(default=None),
):
    """List vocabulary words with pagination."""
    words = db.get_all_words(settings.db_path, theme=theme)

    # Calculate pagination
    total = len(words)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    paginated_words = words[start:end]

    # Convert to response models
    items = [
        VocabularyWord(
            id=w["id"],
            word=w["word"],
            lemma=w["lemma"],
            # ... other fields
        )
        for w in paginated_words
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
```

**Key patterns:**

1. **Query parameters for filtering/pagination**
   ```python
   page: int = Query(default=1, ge=1)  # Page number, at least 1
   page_size: int = Query(default=50, ge=1, le=100)  # Items per page
   theme: Optional[str] = Query(default=None)  # Optional filter
   ```

2. **Pagination logic**
   ```python
   total = len(words)
   total_pages = (total + page_size - 1) // page_size  # Ceiling division
   start = (page - 1) * page_size
   end = start + page_size
   paginated_words = words[start:end]
   ```

3. **Response model conversion**
   ```python
   items = [VocabularyWord(...) for w in paginated_words]
   ```

### Getting a Single Resource (GET one)

```python
@router.get("/{word_id}", response_model=VocabularyWord)
def get_word(word_id: int):
    """Get a single vocabulary word by ID."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang,
               examples, source, theme, added_at
        FROM vocabulary
        WHERE id = ?
        """,
        (word_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Word not found")

    word_dict = dict(row)
    if word_dict["examples"]:
        import json
        word_dict["examples"] = json.loads(word_dict["examples"])
    else:
        word_dict["examples"] = []

    return VocabularyWord(**word_dict)
```

**Key patterns:**

1. **Path parameter for ID**
   ```python
   @router.get("/{word_id}")
   def get_word(word_id: int):  # Automatic type conversion
   ```

2. **404 for not found**
   ```python
   if not row:
       raise HTTPException(status_code=404, detail="Word not found")
   ```

3. **Data transformation**
   ```python
   # JSON stored as string in DB, needs parsing
   word_dict["examples"] = json.loads(word_dict["examples"])
   ```

---

## Create Operations

### Creating a Resource (POST)

From `api/routers/themes.py`:

```python
@router.post("", response_model=TaskStatus)
async def create_theme(request: ThemeCreateRequest):
    """Create a new themed vocabulary set."""
    task_id = task_manager.create_task(TaskType.THEME_CREATE)

    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _create_theme_vocabulary,
            request.description,
            request.source_lang,
            request.target_lang,
            request.word_count,
        )
    )

    return task_manager.get_task(task_id)
```

**Key patterns:**

1. **Request body with Pydantic model**
   ```python
   async def create_theme(request: ThemeCreateRequest):
   ```

2. **Return created resource (or task for async operations)**
   ```python
   return task_manager.get_task(task_id)  # Returns task status
   ```

For simpler creates without background tasks:

```python
@router.post("", response_model=VocabularyWord, status_code=201)
def create_word(request: VocabularyWordCreate):
    """Create a new vocabulary word."""
    word_id = db.add_word(
        word=request.word,
        lemma=request.lemma,
        translation=request.translation,
        # ...
    )
    return db.get_word(word_id)
```

**Note:** `status_code=201` indicates "Created" (instead of default 200 "OK").

---

## Delete Operations

### Deleting a Resource (DELETE)

From `api/routers/vocabulary.py`:

```python
@router.delete("/{word_id}")
def delete_word(word_id: int):
    """Delete a vocabulary word by ID."""
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()

    # Check if word exists first
    cursor.execute("SELECT id FROM vocabulary WHERE id = ?", (word_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Word not found")

    # Delete the word
    cursor.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()

    return {"message": "Word deleted successfully"}
```

**Key patterns:**

1. **Check existence before deleting**
   ```python
   cursor.execute("SELECT id FROM vocabulary WHERE id = ?", (word_id,))
   if not cursor.fetchone():
       raise HTTPException(status_code=404, detail="Word not found")
   ```

2. **Return confirmation message**
   ```python
   return {"message": "Word deleted successfully"}
   ```

**Alternative:** Return 204 No Content:

```python
from fastapi import Response

@router.delete("/{word_id}", status_code=204)
def delete_word(word_id: int):
    # ... delete logic ...
    return Response(status_code=204)
```

---

## Update Operations

While our codebase doesn't have explicit update endpoints, here's how they work:

### Full Update (PUT)

Replaces the entire resource:

```python
@router.put("/{word_id}", response_model=VocabularyWord)
def update_word(word_id: int, request: VocabularyWordUpdate):
    """Replace a vocabulary word entirely."""
    # Check exists
    existing = db.get_word(word_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Word not found")

    # Update all fields
    db.update_word(
        word_id=word_id,
        word=request.word,
        lemma=request.lemma,
        translation=request.translation,
        # All fields must be provided
    )

    return db.get_word(word_id)
```

### Partial Update (PATCH)

Updates only provided fields:

```python
@router.patch("/{word_id}", response_model=VocabularyWord)
def patch_word(word_id: int, request: VocabularyWordPatch):
    """Update specific fields of a vocabulary word."""
    existing = db.get_word(word_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Word not found")

    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    db.update_word(word_id=word_id, **update_data)

    return db.get_word(word_id)
```

**The difference:**
- PUT: Client sends complete object, server replaces everything
- PATCH: Client sends only changed fields, server merges

---

## Pagination Pattern Deep Dive

Our paginated response includes helpful metadata:

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]      # The actual data
    total: int          # Total number of items
    page: int           # Current page number
    page_size: int      # Items per page
    total_pages: int    # Total number of pages
```

**Response example:**

```json
{
  "items": [
    {"id": 1, "word": "casa", ...},
    {"id": 2, "word": "perro", ...}
  ],
  "total": 156,
  "page": 2,
  "page_size": 10,
  "total_pages": 16
}
```

**Why this matters for the frontend:**

```typescript
// Frontend can show:
// "Showing 11-20 of 156 words"
// And render pagination controls:
// [<] [1] [2] [3] ... [16] [>]
```

---

## Error Handling Pattern

Consistent error responses make frontend development easier:

```python
# 404 - Resource not found
raise HTTPException(status_code=404, detail="Word not found")

# 400 - Bad request (invalid input)
raise HTTPException(status_code=400, detail="Invalid URL format")

# 422 - Validation error (handled automatically by Pydantic)

# 500 - Server error
raise HTTPException(status_code=500, detail="Database connection failed")
```

**All errors return the same format:**

```json
{
  "detail": "Error message here"
}
```

---

## Route Order Matters

FastAPI matches routes in order. Be careful with path parameters:

```python
# WRONG ORDER - "/stats" would never match!
@router.get("/{word_id}")  # Matches EVERYTHING including "stats"
def get_word(word_id: int): ...

@router.get("/stats")  # Never reached
def get_stats(): ...

# CORRECT ORDER - specific routes first
@router.get("/stats")  # Matches exactly "/stats"
def get_stats(): ...

@router.get("/{word_id}")  # Matches other paths like "/123"
def get_word(word_id: int): ...
```

---

## Summary: CRUD Patterns

| Operation | Decorator | Success Code | Returns |
|-----------|-----------|--------------|---------|
| List | `@router.get("")` | 200 | Paginated list |
| Get one | `@router.get("/{id}")` | 200 | Single item |
| Create | `@router.post("")` | 201 | Created item |
| Update | `@router.put("/{id}")` | 200 | Updated item |
| Patch | `@router.patch("/{id}")` | 200 | Updated item |
| Delete | `@router.delete("/{id}")` | 200 or 204 | Message or empty |

---

## Try It Yourself

Using the interactive docs (`http://localhost:8000/docs`):

1. **List words**: GET `/api/vocabulary` with different page/page_size
2. **Get one word**: GET `/api/vocabulary/1`
3. **Try a 404**: GET `/api/vocabulary/999999`
4. **Delete a word**: DELETE `/api/vocabulary/1` (careful, this is permanent!)

Or with curl:

```bash
# List with pagination
curl "http://localhost:8000/api/vocabulary?page=1&page_size=5"

# Get single word
curl "http://localhost:8000/api/vocabulary/1"

# Delete (use -X for method)
curl -X DELETE "http://localhost:8000/api/vocabulary/1"
```

---

## What's Next?

Some operations take too long to complete in a single request (like extracting vocabulary from an article using an LLM). [Chapter 7: Background Tasks](07-background-tasks.md) explains how to handle these long-running operations.

---

[← Previous: Routers and Organization](05-routers-and-organization.md) | [Back to Index](README.md) | [Next: Background Tasks →](07-background-tasks.md)
