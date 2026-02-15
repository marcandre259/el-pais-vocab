# Chapter 13: Mutations and Forms

[← Previous: Fetching Data with React Query](12-fetching-data-with-react-query.md) | [Back to Index](README.md) | [Next: Custom Hooks →](14-custom-hooks.md)

---

## useQuery vs useMutation

| useQuery | useMutation |
|----------|-------------|
| For reading data | For writing data |
| Runs automatically | Runs on demand |
| Caches results | No automatic caching |
| GET requests | POST, PUT, DELETE |

---

## useMutation Basics

```tsx
import { useMutation } from '@tanstack/react-query';

function DeleteButton({ wordId }) {
  const mutation = useMutation({
    mutationFn: () => deleteWord(wordId),
    onSuccess: () => {
      console.log('Deleted!');
    },
    onError: (error) => {
      console.error('Failed:', error);
    },
  });

  return (
    <button
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? 'Deleting...' : 'Delete'}
    </button>
  );
}
```

**Key differences from useQuery:**
- Doesn't run automatically - call `mutation.mutate()`
- `isPending` instead of `isLoading`
- Takes data as argument: `mutation.mutate(data)`

---

## Real Example: ArticleForm

From `frontend/src/components/ArticleForm.tsx`:

```tsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { extractArticle } from '../api/client';
import type { ArticleExtractRequest } from '../api/types';

interface ArticleFormProps {
  onTaskStart: (taskId: string) => void;
  disabled?: boolean;
}

export function ArticleForm({ onTaskStart, disabled }: ArticleFormProps) {
  // Form state
  const [url, setUrl] = useState('');
  const [browser, setBrowser] = useState('firefox');
  const [sourceLang, setSourceLang] = useState('Spanish');
  const [targetLang, setTargetLang] = useState('French');
  const [wordCount, setWordCount] = useState('30');
  const [error, setError] = useState<string | null>(null);

  // Mutation for API call
  const mutation = useMutation({
    mutationFn: extractArticle,
    onSuccess: (data) => {
      onTaskStart(data.task_id);  // Notify parent of task
      setUrl('');                  // Clear form
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : 'Extraction failed');
    },
  });

  // Form submission
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (!url.trim()) {
      setError('Please enter an article URL');
      return;
    }

    // Build request and submit
    const request: ArticleExtractRequest = {
      url: url.trim(),
      browser,
      source_lang: sourceLang,
      target_lang: targetLang,
      word_count: parseInt(wordCount, 10) || 30,
    };

    mutation.mutate(request);
  };

  const isLoading = mutation.isPending || disabled;

  return (
    <form onSubmit={handleSubmit}>
      <Input
        label="Article URL"
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={isLoading}
        error={error && !url.trim() ? error : undefined}
      />

      {error && url.trim() && <p className={styles.error}>{error}</p>}

      <Button type="submit" loading={mutation.isPending} disabled={isLoading}>
        Extract Vocabulary
      </Button>
    </form>
  );
}
```

---

## Form State with useState

Multiple `useState` calls manage form fields:

```tsx
const [url, setUrl] = useState('');
const [browser, setBrowser] = useState('firefox');
const [sourceLang, setSourceLang] = useState('Spanish');
const [wordCount, setWordCount] = useState('30');
const [error, setError] = useState<string | null>(null);
```

**Connecting to inputs:**

```tsx
<Input
  value={url}                           // Controlled value
  onChange={(e) => setUrl(e.target.value)}  // Update on change
/>

<Select
  value={browser}
  onChange={(e) => setBrowser(e.target.value)}
/>
```

**This is called "controlled components"** - React controls the input value.

---

## Form Submission

```tsx
const handleSubmit = (e: FormEvent) => {
  // 1. Prevent page reload
  e.preventDefault();

  // 2. Clear previous errors
  setError(null);

  // 3. Validate
  if (!url.trim()) {
    setError('Please enter an article URL');
    return;
  }

  // 4. Build request object
  const request: ArticleExtractRequest = {
    url: url.trim(),
    browser,
    source_lang: sourceLang,
    target_lang: targetLang,
    word_count: parseInt(wordCount, 10) || 30,
  };

  // 5. Submit via mutation
  mutation.mutate(request);
};
```

---

## Mutation Callbacks

`useMutation` provides lifecycle callbacks:

```tsx
const mutation = useMutation({
  mutationFn: extractArticle,

  // Called before mutation starts
  onMutate: (variables) => {
    console.log('Starting with:', variables);
  },

  // Called on success
  onSuccess: (data, variables) => {
    console.log('Success! Result:', data);
    // data = what mutationFn returned
    // variables = what you passed to mutate()
  },

  // Called on error
  onError: (error, variables) => {
    console.error('Failed:', error);
  },

  // Called after success or error
  onSettled: (data, error, variables) => {
    console.log('Done, success or failure');
  },
});
```

---

## Mutation State

```tsx
const mutation = useMutation({ ... });

mutation.isPending;   // Currently running
mutation.isSuccess;   // Completed successfully
mutation.isError;     // Failed
mutation.error;       // Error object if failed
mutation.data;        // Result data if successful
mutation.reset();     // Reset to initial state
```

**Using in UI:**

```tsx
<Button
  type="submit"
  loading={mutation.isPending}
  disabled={mutation.isPending}
>
  {mutation.isPending ? 'Submitting...' : 'Submit'}
</Button>

{mutation.isError && (
  <p className="error">{mutation.error.message}</p>
)}
```

---

## Client-Side Validation

Validate before sending to server:

```tsx
const handleSubmit = (e: FormEvent) => {
  e.preventDefault();
  setError(null);

  // Validation rules
  if (!url.trim()) {
    setError('Please enter an article URL');
    return;
  }

  if (!url.startsWith('http')) {
    setError('Please enter a valid URL');
    return;
  }

  const count = parseInt(wordCount, 10);
  if (isNaN(count) || count < 1 || count > 100) {
    setError('Word count must be 1-100');
    return;
  }

  // All valid, submit
  mutation.mutate({ url, wordCount: count, ... });
};
```

**Benefits:**
- Instant feedback (no server round-trip)
- Reduces invalid API calls
- Better user experience

---

## Error Display Patterns

```tsx
// Global error for the form
{error && <p className={styles.error}>{error}</p>}

// Per-field error
<Input
  label="URL"
  value={url}
  error={!url.trim() ? 'Required' : undefined}
/>

// Mutation error
{mutation.isError && (
  <Alert type="error">
    {mutation.error.message}
  </Alert>
)}
```

---

## Disabling During Submission

Prevent double-submission and show loading state:

```tsx
const isLoading = mutation.isPending || disabled;

return (
  <form>
    <Input disabled={isLoading} ... />
    <Select disabled={isLoading} ... />
    <Button
      type="submit"
      loading={mutation.isPending}
      disabled={isLoading}
    >
      Submit
    </Button>
  </form>
);
```

---

## Invalidating Queries After Mutation

After creating/updating/deleting, refresh related queries:

```tsx
import { useQueryClient, useMutation } from '@tanstack/react-query';

function DeleteWordButton({ wordId }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => deleteWord(wordId),
    onSuccess: () => {
      // Invalidate and refetch vocabulary queries
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });

  return <button onClick={() => mutation.mutate()}>Delete</button>;
}
```

**What happens:**
1. Mutation succeeds
2. `invalidateQueries` marks cached data as stale
3. React Query refetches in background
4. UI updates with fresh data

---

## Summary

| Concept | Purpose |
|---------|---------|
| `useMutation` | For create/update/delete operations |
| `mutation.mutate(data)` | Trigger the mutation |
| `isPending` | Show loading state |
| `onSuccess/onError` | Handle results |
| `invalidateQueries` | Refresh related data |
| Controlled inputs | React manages input values |
| Client validation | Check before submitting |

---

## Form Pattern Summary

```tsx
function MyForm() {
  // 1. State for each field
  const [field, setField] = useState('');
  const [error, setError] = useState(null);

  // 2. Mutation for API call
  const mutation = useMutation({
    mutationFn: apiCall,
    onSuccess: () => { /* clear form, notify parent */ },
    onError: (e) => setError(e.message),
  });

  // 3. Submit handler with validation
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    mutation.mutate({ field });
  };

  // 4. Render form with disabled state
  return (
    <form onSubmit={handleSubmit}>
      <Input value={field} onChange={...} disabled={mutation.isPending} />
      <Button loading={mutation.isPending}>Submit</Button>
    </form>
  );
}
```

---

## Try It Yourself

1. Open `frontend/src/components/ArticleForm.tsx`
2. Trace the flow from form submission to API call
3. Try adding a new validation rule
4. Add `console.log` in mutation callbacks to see the flow

---

## What's Next?

Notice how `useMutation` and `useQuery` share patterns? [Chapter 14: Custom Hooks](14-custom-hooks.md) shows how to extract common logic into reusable hooks.

---

[← Previous: Fetching Data with React Query](12-fetching-data-with-react-query.md) | [Back to Index](README.md) | [Next: Custom Hooks →](14-custom-hooks.md)
