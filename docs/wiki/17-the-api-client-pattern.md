# Chapter 17: The API Client Pattern

[← Previous: Styling with CSS](16-styling-with-css.md) | [Back to Index](README.md) | [Next: Async Workflows →](18-async-workflows.md)

---

## Why Centralize API Calls?

Without a client, API calls are scattered:

```tsx
// In Component A
fetch('/api/vocabulary').then(res => res.json())

// In Component B
fetch('/api/vocabulary').then(res => res.json())

// In Component C - oops, typo!
fetch('/api/vocabulry').then(res => res.json())
```

**Problems:**
- Duplicated fetch logic
- Inconsistent error handling
- Easy to make typos
- Hard to change base URL

---

## The API Client

From `frontend/src/api/client.ts`:

```tsx
import type {
  TaskStatus,
  VocabularyWord,
  PaginatedResponse,
  ArticleExtractRequest,
  // ...
} from './types';

const API_BASE = '/api';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `Request failed: ${response.statusText}`
    );
  }

  return response.json();
}
```

---

## Breaking Down the Request Function

**1. Build the URL:**

```tsx
const url = `${API_BASE}${endpoint}`;
// API_BASE = '/api'
// endpoint = '/vocabulary'
// url = '/api/vocabulary'
```

**2. Make the request with headers:**

```tsx
const response = await fetch(url, {
  ...options,  // method, body, etc.
  headers: {
    'Content-Type': 'application/json',
    ...options.headers,  // Additional headers
  },
});
```

**3. Handle errors:**

```tsx
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  throw new ApiError(
    response.status,
    errorData.detail || `Request failed: ${response.statusText}`
  );
}
```

- `response.ok` is false for 4xx and 5xx status codes
- Extract error message from response body
- Throw typed error with status code

**4. Return typed data:**

```tsx
return response.json();  // Type T inferred from caller
```

---

## Typed API Methods

Each endpoint gets a typed function:

```tsx
// GET /api/tasks/{taskId}
export async function getTask(taskId: string): Promise<TaskStatus> {
  return request<TaskStatus>(`/tasks/${taskId}`);
}

// GET /api/vocabulary with pagination
export async function getVocabulary(
  page = 1,
  pageSize = 50,
  theme?: string
): Promise<PaginatedResponse<VocabularyWord>> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (theme) params.set('theme', theme);
  return request<PaginatedResponse<VocabularyWord>>(`/vocabulary?${params}`);
}

// GET /api/vocabulary/stats
export async function getVocabularyStats(theme?: string): Promise<VocabularyStats> {
  const params = theme ? `?theme=${theme}` : '';
  return request<VocabularyStats>(`/vocabulary/stats${params}`);
}

// DELETE /api/vocabulary/{wordId}
export async function deleteWord(wordId: number): Promise<void> {
  await request(`/vocabulary/${wordId}`, { method: 'DELETE' });
}
```

---

## POST Requests with Bodies

```tsx
// POST /api/articles/extract
export async function extractArticle(
  data: ArticleExtractRequest
): Promise<TaskStatus> {
  return request<TaskStatus>('/articles/extract', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// POST /api/themes
export async function createTheme(
  data: ThemeCreateRequest
): Promise<TaskStatus> {
  return request<TaskStatus>('/themes', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// POST /api/sync/anki
export async function syncToAnki(data: SyncRequest): Promise<TaskStatus> {
  return request<TaskStatus>('/sync/anki', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

---

## Types Matching Backend

The frontend types mirror the backend Pydantic models:

**Backend (Python):**

```python
class VocabularyWord(BaseModel):
    id: int
    word: str
    lemma: str
    pos: Optional[str] = None
    translation: str
    examples: list[str] = []
    theme: str
```

**Frontend (TypeScript):**

```typescript
export interface VocabularyWord {
  id: number;
  word: string;
  lemma: string;
  pos?: string;
  translation: string;
  examples: string[];
  theme: string;
}
```

**Why this matters:**
- TypeScript catches type mismatches at compile time
- IDE autocomplete works correctly
- Refactoring is safer

---

## URL Helper Functions

For URLs that aren't fetched via `request`:

```tsx
// Returns URL string, not a fetch
export function getAudioUrl(lemma: string): string {
  return `${API_BASE}/audio/${encodeURIComponent(lemma)}.mp3`;
}
```

Usage:

```tsx
<audio src={getAudioUrl(word.lemma)} />
```

---

## Error Handling

The custom `ApiError` class carries status information:

```tsx
class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}
```

Usage in components:

```tsx
import { ApiError } from '../api/client';

const mutation = useMutation({
  mutationFn: extractArticle,
  onError: (error) => {
    if (error instanceof ApiError) {
      if (error.status === 404) {
        setError('Article not found');
      } else if (error.status === 403) {
        setError('Access denied - check your login');
      } else {
        setError(error.message);
      }
    }
  },
});
```

---

## Proxy Configuration

During development, API calls go through the Vite proxy:

```
Browser                  Vite Dev Server           FastAPI
  │                           │                       │
  │ fetch('/api/vocab')       │                       │
  │ ─────────────────────────►│                       │
  │                           │ Forward to :8000      │
  │                           │──────────────────────►│
  │                           │                       │
  │                           │◄──────────────────────│
  │◄─────────────────────────│                       │
```

From `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

This is why we can use `/api` without specifying the full `http://localhost:8000`.

---

## Complete API Client

```tsx
// Types
import type { TaskStatus, VocabularyWord, ... } from './types';

// Base configuration
const API_BASE = '/api';

// Error class
class ApiError extends Error { ... }

// Generic request function
async function request<T>(endpoint: string, options?: RequestInit): Promise<T>

// API methods by resource
// Tasks
export async function getTask(taskId: string): Promise<TaskStatus>

// Vocabulary
export async function getVocabulary(...): Promise<PaginatedResponse<VocabularyWord>>
export async function getVocabularyStats(...): Promise<VocabularyStats>
export async function deleteWord(wordId: number): Promise<void>

// Articles
export async function extractArticle(data): Promise<TaskStatus>

// Themes
export async function getThemes(): Promise<Theme[]>
export async function createTheme(data): Promise<TaskStatus>

// Audio
export function getAudioUrl(lemma: string): string

// Sync
export async function checkAnkiStatus(): Promise<SyncStatus>
export async function syncToAnki(data): Promise<TaskStatus>

// Export error class
export { ApiError };
```

---

## Summary

| Pattern | Purpose |
|---------|---------|
| **Centralized client** | Single source for all API calls |
| **Generic request** | Reusable fetch logic with error handling |
| **Typed methods** | Type-safe API calls |
| **ApiError class** | Rich error information |
| **URL helpers** | Non-fetch URL generation |

---

## Benefits

1. **Type safety** - TypeScript catches mismatches
2. **Consistency** - All requests handled the same way
3. **Maintainability** - Change base URL in one place
4. **Discoverability** - All endpoints in one file
5. **Testing** - Easy to mock the client

---

## Try It Yourself

1. Open `frontend/src/api/client.ts`
2. Trace how `extractArticle` flows from component to server
3. Add console.log in `request` to see all API calls
4. Try adding a new API method for a hypothetical endpoint

---

## What's Next?

We've seen how the client makes requests. [Chapter 18: Async Workflows](18-async-workflows.md) shows how everything connects for long-running operations.

---

[← Previous: Styling with CSS](16-styling-with-css.md) | [Back to Index](README.md) | [Next: Async Workflows →](18-async-workflows.md)
