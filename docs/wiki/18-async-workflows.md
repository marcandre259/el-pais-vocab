# Chapter 18: Async Workflows

[← Previous: The API Client Pattern](17-the-api-client-pattern.md) | [Back to Index](README.md) | [Next: SQLite Basics →](19-sqlite-basics.md)

---

## The Complete Picture

This chapter ties together everything we've learned to show how a long-running operation flows through the entire stack.

**The workflow:** User submits article URL → Backend extracts vocabulary → Frontend shows result

---

## Step 1: User Submits Form

```tsx
// ArticleForm.tsx
const mutation = useMutation({
  mutationFn: extractArticle,  // API client function
  onSuccess: (data) => {
    onTaskStart(data.task_id);  // Pass task ID to parent
    setUrl('');                  // Clear form
  },
});

const handleSubmit = (e: FormEvent) => {
  e.preventDefault();

  const request: ArticleExtractRequest = {
    url: url.trim(),
    browser,
    source_lang: sourceLang,
    target_lang: targetLang,
    word_count: parseInt(wordCount, 10),
  };

  mutation.mutate(request);  // Trigger the mutation
};
```

---

## Step 2: API Client Sends Request

```tsx
// api/client.ts
export async function extractArticle(
  data: ArticleExtractRequest
): Promise<TaskStatus> {
  return request<TaskStatus>('/articles/extract', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

**HTTP Request:**
```
POST /api/articles/extract
Content-Type: application/json

{
  "url": "https://elpais.com/...",
  "browser": "firefox",
  "source_lang": "Spanish",
  "target_lang": "French",
  "word_count": 30
}
```

---

## Step 3: Backend Creates Task

```python
# api/routers/articles.py
@router.post("/extract", response_model=TaskStatus)
async def extract_vocabulary(request: ArticleExtractRequest):
    # Create task record
    task_id = task_manager.create_task(TaskType.ARTICLE_EXTRACT)

    # Start background execution (doesn't wait)
    asyncio.create_task(
        task_manager.run_task(
            task_id,
            _extract_article_vocabulary,  # Sync function
            request.url,
            request.browser,
            request.source_lang,
            request.target_lang,
            request.word_count,
            request.prompt,
        )
    )

    # Return immediately with task status
    return task_manager.get_task(task_id)
```

**HTTP Response (immediate):**
```json
{
  "task_id": "abc-123-def",
  "type": "article_extract",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Step 4: Background Work Runs

```python
# api/services/task_manager.py
async def run_task(self, task_id: str, func: Callable, *args, **kwargs):
    # Update status
    self.update_task(task_id, status=TaskStatusEnum.IN_PROGRESS)

    loop = asyncio.get_event_loop()
    try:
        # Run sync function in thread pool
        result = await loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )
        self.update_task(task_id, status=TaskStatusEnum.COMPLETED, result=result)
    except Exception as e:
        self.update_task(task_id, status=TaskStatusEnum.FAILED, error=str(e))
```

**Meanwhile, the actual work:**
```python
def _extract_article_vocabulary(url, browser, source_lang, ...):
    # 1. Fetch article (2-5 seconds)
    article_text = scraper.get_article_text(url, browser)

    # 2. Call LLM for extraction (10-20 seconds)
    words = llm.select_and_translate(article_text, ...)

    # 3. Save to database
    new_count, updated_count = db.add_words(words, ...)

    # 4. Return result
    return {
        "new_words": new_count,
        "updated_words": updated_count,
        "words": words,
        "source_url": url,
    }
```

---

## Step 5: Frontend Starts Polling

```tsx
// hooks/useTask.ts
export function useTask(taskId: string | null) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Keep polling while task is running
      if (data && ['pending', 'in_progress'].includes(data.status)) {
        return 1000;  // Poll every second
      }
      return false;  // Stop polling
    },
  });
}
```

---

## Step 6: Backend Returns Status

```python
# api/routers/tasks.py
@router.get("/{task_id}", response_model=TaskStatus)
def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

**Poll 1 (1 second after start):**
```json
{
  "task_id": "abc-123-def",
  "status": "in_progress",
  "progress": null
}
```

**Poll 5 (5 seconds after start):**
```json
{
  "task_id": "abc-123-def",
  "status": "in_progress"
}
```

**Poll 15 (15 seconds after start - completed):**
```json
{
  "task_id": "abc-123-def",
  "status": "completed",
  "result": {
    "new_words": 8,
    "updated_words": 2,
    "words": [...],
    "source_url": "https://elpais.com/..."
  },
  "completed_at": "2024-01-15T10:30:15"
}
```

---

## Step 7: Frontend Shows Result

```tsx
// Home.tsx
const { data: task } = useTask(taskId);

// TaskProgress component
function TaskProgress({ task }) {
  if (!task) return null;

  if (task.status === 'pending' || task.status === 'in_progress') {
    return <Spinner label="Extracting vocabulary..." />;
  }

  if (task.status === 'failed') {
    return <ErrorMessage error={task.error} />;
  }

  if (task.status === 'completed') {
    const result = task.result as ArticleExtractResult;
    return (
      <SuccessMessage>
        Added {result.new_words} new words,
        updated {result.updated_words} existing words.
      </SuccessMessage>
    );
  }
}
```

---

## Visual Timeline

```
Time    Frontend                    Backend
─────   ────────────────────        ────────────────────
0s      Form submit
        └─► POST /extract
                                    Create task (pending)
                                    Start background job
        ◄── {status: "pending"}     Return immediately

        Start polling
        └─► GET /tasks/abc
                                    └─► {status: "in_progress"}

2s      └─► GET /tasks/abc
                                    └─► {status: "in_progress"}
        Show "Extracting..."

5s      └─► GET /tasks/abc          Background: fetching article
                                    └─► {status: "in_progress"}

10s     └─► GET /tasks/abc          Background: calling LLM
                                    └─► {status: "in_progress"}

15s     └─► GET /tasks/abc          Background: saving results
                                    Update task (completed)
                                    └─► {status: "completed", result: {...}}

        Stop polling
        Show "Added 8 words!"
```

---

## Coordinating State

The Home page coordinates form and task:

```tsx
// pages/Home.tsx
export function Home() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const { data: task } = useTask(taskId);

  // Form submits → get task ID
  const handleTaskStart = (id: string) => {
    setTaskId(id);
  };

  // User dismisses result → clear task
  const handleDismiss = () => {
    setTaskId(null);
  };

  // Disable forms while task is running
  const isTaskRunning = task?.status === 'pending' || task?.status === 'in_progress';

  return (
    <div>
      <ArticleForm
        onTaskStart={handleTaskStart}
        disabled={isTaskRunning}
      />

      {task && (
        <TaskProgress
          task={task}
          onDismiss={handleDismiss}
        />
      )}
    </div>
  );
}
```

---

## Error Handling Across the Stack

**Backend error:**
```python
def _extract_article_vocabulary(url, ...):
    try:
        article_text = scraper.get_article_text(url, browser)
    except Exception as e:
        raise Exception(f"Could not fetch article: {e}")
```

**Task manager catches it:**
```python
except Exception as e:
    self.update_task(task_id, status=TaskStatusEnum.FAILED, error=str(e))
```

**Frontend displays it:**
```tsx
if (task.status === 'failed') {
  return <ErrorMessage>{task.error}</ErrorMessage>;
}
```

---

## Summary: The Full Stack

| Layer | Responsibility |
|-------|---------------|
| **Form Component** | Collect input, validate, submit |
| **useMutation** | Handle submission state |
| **API Client** | Make HTTP request |
| **FastAPI Router** | Create task, start background work |
| **Task Manager** | Track status, run in thread pool |
| **Core Modules** | Actual business logic |
| **useTask Hook** | Poll for status |
| **Progress Component** | Display status to user |

---

## Why This Pattern?

1. **Responsive UI** - Form submits instantly
2. **User feedback** - Progress shown during long operation
3. **Error recovery** - Errors are captured and displayed
4. **Server efficiency** - HTTP connections don't hang
5. **Scalable** - Can handle many concurrent tasks

---

## Try It Yourself

1. Open browser Network tab
2. Submit an article URL
3. Watch the initial POST return immediately
4. Watch the GET /tasks polling
5. See the final response with results

Add `console.log` statements at each layer to trace the full flow.

---

## What's Next?

We've seen the full flow. [Chapter 19: SQLite Basics](19-sqlite-basics.md) dives into how data is stored in the database.

---

[← Previous: The API Client Pattern](17-the-api-client-pattern.md) | [Back to Index](README.md) | [Next: SQLite Basics →](19-sqlite-basics.md)
