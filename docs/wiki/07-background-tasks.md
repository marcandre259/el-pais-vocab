# Chapter 7: Background Tasks

[← Previous: CRUD Operations](06-crud-operations.md) | [Back to Index](README.md) | [Next: Configuration and Settings →](08-configuration-and-settings.md)

---

## Why Background Tasks?

Some operations take too long for a normal HTTP request:

| Operation | Typical Time | Problem |
|-----------|--------------|---------|
| Database query | 10-100ms | Fine |
| File read | 50-200ms | Fine |
| LLM API call | 5-30 seconds | Too long! |
| Audio generation | 10-60 seconds | Too long! |

HTTP requests typically timeout after 30-60 seconds. Users don't want to stare at a spinner for 30 seconds with no feedback.

**Solution:** Start the task, return immediately, let the client poll for results.

---

## The Pattern: Create → Poll → Complete

```
┌──────────┐         POST /extract              ┌──────────┐
│          │ ───────────────────────────────────►           │
│  Client  │         {task_id: "abc123"}        │  Server  │
│          │ ◄─────────────────────────────────── (instant) │
└──────────┘                                    └──────────┘
     │                                               │
     │ (task runs in background)                     │
     │                                               │
     │         GET /tasks/abc123                     │
     │ ───────────────────────────────────────────►  │
     │         {status: "in_progress"}               │
     │ ◄───────────────────────────────────────────  │
     │                                               │
     │         GET /tasks/abc123                     │
     │ ───────────────────────────────────────────►  │
     │         {status: "completed", result: {...}}  │
     │ ◄───────────────────────────────────────────  │
```

**Steps:**
1. Client sends request to start operation
2. Server creates a task, returns task ID immediately
3. Server runs the actual work in the background
4. Client polls task status until complete
5. Client retrieves the result

---

## The Task Manager

From `api/services/task_manager.py`:

```python
import uuid
import asyncio
from datetime import datetime
from typing import Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor

from api.schemas.tasks import TaskStatus, TaskType, TaskStatusEnum


class TaskManager:
    """In-memory background task manager."""

    def __init__(self, max_workers: int = 4):
        self._tasks: dict[str, TaskStatus] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
```

**Key components:**
- `_tasks`: Dictionary storing task states (in memory)
- `_executor`: Thread pool for running synchronous code

---

## Creating a Task

```python
def create_task(self, task_type: TaskType) -> str:
    """Create a new pending task and return its ID."""
    task_id = str(uuid.uuid4())
    self._tasks[task_id] = TaskStatus(
        task_id=task_id,
        type=task_type,
        status=TaskStatusEnum.PENDING,
        created_at=datetime.now(),
    )
    return task_id
```

**What happens:**
1. Generate unique ID (UUID)
2. Create task with PENDING status
3. Store in dictionary
4. Return ID to caller

---

## Running a Task

```python
async def run_task(
    self,
    task_id: str,
    func: Callable,
    *args,
    **kwargs,
) -> None:
    """Run a synchronous function in background thread pool."""
    self.update_task(task_id, status=TaskStatusEnum.IN_PROGRESS)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            self._executor, lambda: func(*args, **kwargs)
        )
        self.update_task(task_id, status=TaskStatusEnum.COMPLETED, result=result)
    except Exception as e:
        self.update_task(task_id, status=TaskStatusEnum.FAILED, error=str(e))
```

**The magic: `run_in_executor`**

This is how you run synchronous (blocking) code without blocking the async event loop:

```python
# This would BLOCK the entire server:
result = slow_sync_function()

# This runs in a thread pool, doesn't block:
result = await loop.run_in_executor(executor, slow_sync_function)
```

**Flow:**
1. Update status to IN_PROGRESS
2. Run function in thread pool (non-blocking)
3. On success: status = COMPLETED, store result
4. On error: status = FAILED, store error message

---

## Task Status States

```python
class TaskStatusEnum(str, Enum):
    PENDING = "pending"         # Created, not started
    IN_PROGRESS = "in_progress" # Currently running
    COMPLETED = "completed"     # Finished successfully
    FAILED = "failed"           # Finished with error
```

**State transitions:**

```
PENDING ──► IN_PROGRESS ──► COMPLETED
                │
                └──► FAILED
```

---

## Using the Task Manager in Routes

From `api/routers/articles.py`:

```python
# Synchronous helper function (the actual work)
def _extract_article_vocabulary(
    url: str,
    browser: str,
    source_lang: str,
    target_lang: str,
    word_count: int,
    prompt: str,
) -> dict:
    """Synchronous function to extract vocabulary from article."""
    # Fetch article text
    article_text = scraper.get_article_text(url, browser)

    # Get known words to exclude
    known_words = db.get_known_lemmas("el_pais", settings.db_path)

    # Extract vocabulary using LLM (this is slow!)
    words = llm.select_and_translate(
        article_text=article_text,
        known_words=known_words,
        # ...
    )

    # Add words to database
    new_count, updated_count = db.add_words(words=words, ...)

    return {
        "new_words": new_count,
        "updated_words": updated_count,
        "words": words,
        "source_url": url,
    }


# Async endpoint (returns immediately)
@router.post("/extract", response_model=TaskStatus)
async def extract_vocabulary(request: ArticleExtractRequest):
    """
    Extract vocabulary from an El País article.

    Returns a task_id to poll for results, as LLM extraction takes 10-30 seconds.
    """
    # 1. Create the task
    task_id = task_manager.create_task(TaskType.ARTICLE_EXTRACT)

    # 2. Start background execution
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _extract_article_vocabulary,
            request.url,
            request.browser,
            request.source_lang,
            request.target_lang,
            request.word_count,
            request.prompt,
        )
    )

    # 3. Return task status immediately
    return task_manager.get_task(task_id)
```

**Key insight:** `asyncio.create_task()` starts the coroutine but doesn't wait for it. The endpoint returns immediately while the task runs in the background.

---

## Polling for Task Status

From `api/routers/tasks.py`:

```python
@router.get("/{task_id}", response_model=TaskStatus)
def get_task(task_id: str):
    """Get the status of a background task."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

**Response examples:**

```json
// Pending
{
  "task_id": "abc-123",
  "type": "article_extract",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}

// In progress
{
  "task_id": "abc-123",
  "type": "article_extract",
  "status": "in_progress",
  "created_at": "2024-01-15T10:30:00"
}

// Completed
{
  "task_id": "abc-123",
  "type": "article_extract",
  "status": "completed",
  "result": {
    "new_words": 8,
    "updated_words": 2,
    "words": [...]
  },
  "created_at": "2024-01-15T10:30:00",
  "completed_at": "2024-01-15T10:30:25"
}

// Failed
{
  "task_id": "abc-123",
  "type": "article_extract",
  "status": "failed",
  "error": "Could not fetch article: 403 Forbidden",
  "created_at": "2024-01-15T10:30:00",
  "completed_at": "2024-01-15T10:30:05"
}
```

---

## Understanding async/await

**Synchronous code (blocking):**

```python
def fetch_data():
    result1 = slow_operation_1()  # Wait 5 seconds
    result2 = slow_operation_2()  # Wait 5 seconds
    return result1, result2       # Total: 10 seconds
```

**Asynchronous code (non-blocking):**

```python
async def fetch_data():
    # Start both operations
    task1 = asyncio.create_task(slow_operation_1())
    task2 = asyncio.create_task(slow_operation_2())

    # Wait for both to complete
    result1 = await task1
    result2 = await task2
    return result1, result2  # Total: 5 seconds (parallel)
```

**Key concepts:**
- `async def` - Defines a coroutine (can be paused/resumed)
- `await` - Pause here until this operation completes
- `asyncio.create_task()` - Start a coroutine without waiting

---

## The ThreadPoolExecutor Bridge

Most Python libraries are synchronous (blocking). The `ThreadPoolExecutor` lets us use them without blocking async code:

```python
# Synchronous function (blocks the thread)
def sync_llm_call(prompt):
    return client.messages.create(...)  # Blocks for 10+ seconds

# In async context
async def async_wrapper():
    loop = asyncio.get_event_loop()

    # Run in thread pool - doesn't block the event loop
    result = await loop.run_in_executor(
        executor,
        sync_llm_call,
        "Hello, Claude!"
    )

    return result
```

**Why this matters:**
- FastAPI is async - it handles many requests concurrently
- If we block the event loop, all requests wait
- Thread pool runs blocking code in separate threads

---

## Task Cleanup

Tasks are stored in memory. Old tasks should be removed:

```python
def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
    """Remove tasks older than max_age_hours. Returns count of removed tasks."""
    now = datetime.now()
    to_remove = []
    for task_id, task in self._tasks.items():
        age = now - task.created_at
        if age.total_seconds() > max_age_hours * 3600:
            to_remove.append(task_id)

    for task_id in to_remove:
        del self._tasks[task_id]

    return len(to_remove)
```

**Note:** This is a simple in-memory implementation. Production systems might use Redis or a database for task storage.

---

## Updating Immutable Pydantic Models

Pydantic models are immutable by default. The task manager handles this by creating new instances:

```python
def update_task(
    self,
    task_id: str,
    status: Optional[TaskStatusEnum] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """Update task status."""
    task = self._tasks[task_id]

    # Create NEW TaskStatus with updated values
    self._tasks[task_id] = TaskStatus(
        task_id=task.task_id,
        type=task.type,
        status=status or task.status,
        result=result if result is not None else task.result,
        error=error if error is not None else task.error,
        created_at=task.created_at,
        completed_at=datetime.now() if status in (COMPLETED, FAILED) else None,
    )
```

---

## Complete Flow Example

Let's trace extracting vocabulary from an article:

```
1. POST /api/articles/extract
   Body: {"url": "https://elpais.com/article"}

2. Server: create_task() → task_id = "abc-123"

3. Server: asyncio.create_task(run_task(...))
   Returns immediately: {"task_id": "abc-123", "status": "pending"}

4. Background thread:
   - Fetches article (2-5 seconds)
   - Calls LLM (10-20 seconds)
   - Saves to database
   - Updates task: status="completed", result={...}

5. Client polls: GET /api/tasks/abc-123
   Response: {"status": "in_progress"}

6. Client polls again: GET /api/tasks/abc-123
   Response: {"status": "completed", "result": {"new_words": 8, ...}}

7. Client shows success message with results
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Task Manager** | Tracks background task states |
| **ThreadPoolExecutor** | Runs sync code without blocking |
| **asyncio.create_task** | Starts task without waiting |
| **run_in_executor** | Bridges sync/async code |
| **Polling** | Client checks status periodically |
| **Task status** | PENDING → IN_PROGRESS → COMPLETED/FAILED |

---

## Try It Yourself

1. Start extracting an article via the API docs
2. Copy the returned `task_id`
3. Poll `/api/tasks/{task_id}` and watch the status change
4. When complete, see the result in the response

Or with curl:

```bash
# Start extraction
curl -X POST "http://localhost:8000/api/articles/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://elpais.com/some-article"}'

# Poll for status (use the task_id from the response)
curl "http://localhost:8000/api/tasks/YOUR-TASK-ID"
```

---

## What's Next?

The task manager uses `settings.db_path` for database location. [Chapter 8: Configuration and Settings](08-configuration-and-settings.md) explains how application configuration works with Pydantic Settings.

---

[← Previous: CRUD Operations](06-crud-operations.md) | [Back to Index](README.md) | [Next: Configuration and Settings →](08-configuration-and-settings.md)
