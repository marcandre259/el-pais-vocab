# Chapter 12: Fetching Data with React Query

[← Previous: TypeScript Essentials](11-typescript-essentials.md) | [Back to Index](README.md) | [Next: Mutations and Forms →](13-mutations-and-forms.md)

---

## The Problem: Managing Server State is Hard

Without a library, fetching data looks like this:

```tsx
function WordList() {
  const [words, setWords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/vocabulary')
      .then(res => res.json())
      .then(data => {
        setWords(data.items);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  return <ul>{words.map(w => <li key={w.id}>{w.word}</li>)}</ul>;
}
```

**Problems:**
- Lots of boilerplate (loading, error states)
- No caching (refetches every mount)
- No automatic refetching
- Hard to invalidate when data changes

---

## React Query to the Rescue

React Query (TanStack Query) handles all of this:

```tsx
import { useQuery } from '@tanstack/react-query';

function WordList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['vocabulary'],
    queryFn: () => fetch('/api/vocabulary').then(res => res.json()),
  });

  if (isLoading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  return <ul>{data.items.map(w => <li key={w.id}>{w.word}</li>)}</ul>;
}
```

**Benefits:**
- Automatic loading/error states
- Caching - same query used elsewhere won't refetch
- Automatic background refetching
- Easy cache invalidation

---

## useQuery Basics

From `frontend/src/pages/Browse.tsx`:

```tsx
import { useQuery } from '@tanstack/react-query';
import { getVocabulary, getVocabularyStats } from '../api/client';

export function Browse() {
  const [page, setPage] = useState(1);
  const [selectedTheme, setSelectedTheme] = useState<string>('');

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', selectedTheme || undefined],
    queryFn: () => getVocabularyStats(selectedTheme || undefined),
  });

  // Fetch vocabulary with pagination
  const { data: vocabulary, isLoading: vocabLoading } = useQuery({
    queryKey: ['vocabulary', page, selectedTheme || undefined],
    queryFn: () => getVocabulary(page, 30, selectedTheme || undefined),
  });

  // ... render
}
```

**Key parameters:**

| Parameter | Purpose |
|-----------|---------|
| `queryKey` | Unique identifier for caching |
| `queryFn` | Function that fetches the data |

---

## Query Keys: How Caching Works

The `queryKey` determines when React Query refetches or uses cache:

```tsx
// These are DIFFERENT queries (different keys)
useQuery({ queryKey: ['vocabulary', 1], ... })  // Page 1
useQuery({ queryKey: ['vocabulary', 2], ... })  // Page 2

// These are the SAME query (same key)
useQuery({ queryKey: ['vocabulary', 1], ... })  // First component
useQuery({ queryKey: ['vocabulary', 1], ... })  // Second component - uses cache
```

**Key structure best practices:**
- Start with a string identifier: `['vocabulary']`
- Add parameters that affect the result: `['vocabulary', page, theme]`
- Object keys work too: `['vocabulary', { page, theme }]`

---

## What useQuery Returns

```tsx
const {
  data,       // The fetched data (undefined until loaded)
  isLoading,  // True on first load (no cached data)
  isFetching, // True whenever fetching (including background)
  error,      // Error object if query failed
  isError,    // Boolean for error state
  isSuccess,  // Boolean for success state
  refetch,    // Function to manually refetch
} = useQuery({ ... });
```

**Loading vs Fetching:**
- `isLoading` - No data yet, show skeleton/spinner
- `isFetching` - Getting fresh data, but may have stale data to show

---

## Stale Time and Refetching

React Query has smart defaults:

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,  // Data fresh for 30 seconds
      retry: 1,          // Retry failed requests once
    },
  },
});
```

**What happens:**
1. First load: Fetch from server, cache result
2. Same query within 30s: Return cached data instantly
3. After 30s: Return cache, fetch fresh data in background
4. Component mounts: Use cache if available
5. Window focus: Refetch stale queries

---

## Real Example: Browse Page

```tsx
export function Browse() {
  const [page, setPage] = useState(1);
  const [selectedTheme, setSelectedTheme] = useState<string>('');

  // Stats query - changes when theme filter changes
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', selectedTheme || undefined],
    queryFn: () => getVocabularyStats(selectedTheme || undefined),
  });

  // Vocabulary query - changes when page or theme changes
  const { data: vocabulary, isLoading: vocabLoading } = useQuery({
    queryKey: ['vocabulary', page, selectedTheme || undefined],
    queryFn: () => getVocabulary(page, 30, selectedTheme || undefined),
  });

  // Themes query - only fetched once
  const { data: themes } = useQuery({
    queryKey: ['themes'],
    queryFn: getThemes,
  });

  // When filter changes, reset to page 1
  const handleThemeChange = (theme: string) => {
    setSelectedTheme(theme);
    setPage(1);
  };

  return (
    <div>
      {statsLoading ? (
        <p>Loading stats...</p>
      ) : stats ? (
        <StatCard label="Total words" value={stats.total_words} />
      ) : null}

      <WordList
        words={vocabulary?.items || []}
        page={page}
        totalPages={vocabulary?.total_pages || 1}
        onPageChange={setPage}
        isLoading={vocabLoading}
      />
    </div>
  );
}
```

**What happens when user changes page:**
1. `page` state changes: 1 → 2
2. Query key changes: `['vocabulary', 1, ...]` → `['vocabulary', 2, ...]`
3. React Query checks cache for new key
4. If not cached: fetches, shows loading
5. If cached: shows cached data, fetches fresh in background

---

## Conditional Queries

Sometimes you only want to fetch under certain conditions:

```tsx
const { data } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => getUser(userId),
  enabled: !!userId,  // Only fetch if userId exists
});
```

From `frontend/src/hooks/useTask.ts`:

```tsx
return useQuery({
  queryKey: ['task', taskId],
  queryFn: () => getTask(taskId!),
  enabled: enabled && !!taskId,  // Only when enabled and taskId exists
  // ...
});
```

---

## Provider Setup

React Query needs a provider at the app root:

From `frontend/src/App.tsx`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,  // 30 seconds
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* Your app */}
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## Dependent Queries

Sometimes one query depends on another:

```tsx
// First query
const { data: user } = useQuery({
  queryKey: ['user'],
  queryFn: getUser,
});

// Second query - depends on first
const { data: posts } = useQuery({
  queryKey: ['posts', user?.id],
  queryFn: () => getPosts(user!.id),
  enabled: !!user?.id,  // Only fetch when user is loaded
});
```

---

## Error Handling

```tsx
const { data, error, isError } = useQuery({
  queryKey: ['vocabulary'],
  queryFn: getVocabulary,
});

if (isError) {
  return <ErrorMessage error={error} />;
}

// Or use error boundaries
const { data } = useQuery({
  queryKey: ['vocabulary'],
  queryFn: getVocabulary,
  throwOnError: true,  // Throw to nearest error boundary
});
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| `useQuery` | Fetch and cache data |
| `queryKey` | Unique identifier for cache |
| `queryFn` | Function that returns data |
| `isLoading` | First load, no data |
| `isFetching` | Any fetch in progress |
| `enabled` | Conditional fetching |
| `staleTime` | How long data stays fresh |

---

## Mental Model

Think of React Query as a smart cache between your UI and API:

```
Component                 React Query                  Server
    │                          │                          │
    │  useQuery(key, fn)       │                          │
    │ ─────────────────────►   │                          │
    │                          │ Check cache              │
    │                          │ ───────────►             │
    │  (cache hit)             │                          │
    │ ◄───────────────────────                            │
    │                          │ Fetch in background      │
    │                          │ ────────────────────────►│
    │                          │ ◄────────────────────────│
    │  (fresh data)            │                          │
    │ ◄───────────────────────                            │
```

---

## Try It Yourself

1. Open the Browse page in the app
2. Open Network tab in dev tools
3. Navigate between pages - notice cached requests don't refetch
4. Wait 30+ seconds and navigate - see background refetch
5. Add `console.log` in a query function to see when it runs

---

## What's Next?

`useQuery` is for reading data. [Chapter 13: Mutations and Forms](13-mutations-and-forms.md) covers `useMutation` for creating, updating, and deleting data.

---

[← Previous: TypeScript Essentials](11-typescript-essentials.md) | [Back to Index](README.md) | [Next: Mutations and Forms →](13-mutations-and-forms.md)
