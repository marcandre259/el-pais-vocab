# Chapter 14: Custom Hooks

[← Previous: Mutations and Forms](13-mutations-and-forms.md) | [Back to Index](README.md) | [Next: Routing with React Router →](15-routing-with-react-router.md)

---

## What Are Hooks?

Hooks are functions that let you use React features:

```tsx
// Built-in hooks
useState()      // State management
useEffect()     // Side effects
useContext()    // Context values
useMemo()       // Memoized values
useCallback()   // Memoized functions

// Library hooks
useQuery()      // React Query
useMutation()   // React Query
useNavigate()   // React Router
```

**The rule:** Hook names start with `use`.

---

## Why Custom Hooks?

Custom hooks let you extract and reuse logic:

**Without custom hook** (duplicated logic):

```tsx
// Component A
function ArticleStatus({ taskId }) {
  const { data } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'pending') return 1000;
      return false;
    },
  });
  // ...
}

// Component B - same logic copied
function ThemeStatus({ taskId }) {
  const { data } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'pending') return 1000;
      return false;
    },
  });
  // ...
}
```

**With custom hook** (reusable):

```tsx
// Custom hook
function useTask(taskId) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
    refetchInterval: (query) => {
      if (query.state.data?.status === 'pending') return 1000;
      return false;
    },
  });
}

// Component A
function ArticleStatus({ taskId }) {
  const { data } = useTask(taskId);
  // ...
}

// Component B
function ThemeStatus({ taskId }) {
  const { data } = useTask(taskId);
  // ...
}
```

---

## Real Example: useTask

From `frontend/src/hooks/useTask.ts`:

```tsx
import { useQuery } from '@tanstack/react-query';
import { getTask } from '../api/client';
import type { TaskStatus } from '../api/types';

interface UseTaskOptions {
  enabled?: boolean;
}

export function useTask(taskId: string | null, options: UseTaskOptions = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId!),
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Keep polling while pending or in_progress
      if (data && ['pending', 'in_progress'].includes(data.status)) {
        return 1000; // Poll every second
      }
      return false; // Stop polling
    },
    refetchIntervalInBackground: false,
  });
}

// Helper functions
export function isTaskRunning(status?: TaskStatus): boolean {
  return status?.status === 'pending' || status?.status === 'in_progress';
}

export function isTaskComplete(status?: TaskStatus): boolean {
  return status?.status === 'completed';
}

export function isTaskFailed(status?: TaskStatus): boolean {
  return status?.status === 'failed';
}
```

---

## Breaking Down useTask

**1. Accept parameters:**

```tsx
function useTask(taskId: string | null, options: UseTaskOptions = {}) {
```

- `taskId` can be null (no task yet)
- `options` for customization

**2. Conditional fetching:**

```tsx
enabled: enabled && !!taskId,
```

Only fetch when:
- `enabled` option is true (default)
- `taskId` exists (not null)

**3. Smart polling:**

```tsx
refetchInterval: (query) => {
  const data = query.state.data;
  if (data && ['pending', 'in_progress'].includes(data.status)) {
    return 1000; // Poll every second
  }
  return false; // Stop polling
},
```

- Poll every second while task is running
- Stop polling when complete or failed
- Saves server resources

**4. Return useQuery result:**

```tsx
return useQuery({ ... });
```

The hook returns everything `useQuery` returns.

---

## Using useTask

```tsx
import { useTask, isTaskComplete, isTaskFailed } from '../hooks/useTask';

function TaskProgress({ taskId }) {
  const { data: task, isLoading } = useTask(taskId);

  if (isLoading) return <Spinner />;
  if (isTaskComplete(task)) return <SuccessMessage result={task.result} />;
  if (isTaskFailed(task)) return <ErrorMessage error={task.error} />;

  return <ProgressIndicator status={task.status} />;
}
```

---

## Custom Hook Rules

1. **Name starts with `use`**
   ```tsx
   function useTask() { ... }     // ✓ Good
   function taskHook() { ... }    // ✗ Bad
   ```

2. **Call hooks at the top level**
   ```tsx
   function useMyHook() {
     // ✓ Good - top level
     const [state, setState] = useState();

     // ✗ Bad - inside condition
     if (condition) {
       const [other, setOther] = useState();
     }
   }
   ```

3. **Only call from React functions**
   ```tsx
   // ✓ Good - in a component
   function MyComponent() {
     const task = useTask(id);
   }

   // ✓ Good - in another hook
   function useMyHook() {
     const task = useTask(id);
   }

   // ✗ Bad - in regular function
   function helper() {
     const task = useTask(id);
   }
   ```

---

## Combining Hooks

Custom hooks can combine multiple hooks:

```tsx
function useFormWithValidation(initialValue, validator) {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState(null);
  const [touched, setTouched] = useState(false);

  const handleChange = (e) => {
    setValue(e.target.value);
    if (touched) {
      setError(validator(e.target.value));
    }
  };

  const handleBlur = () => {
    setTouched(true);
    setError(validator(value));
  };

  return {
    value,
    error: touched ? error : null,
    onChange: handleChange,
    onBlur: handleBlur,
  };
}

// Usage
function MyForm() {
  const email = useFormWithValidation('', validateEmail);

  return (
    <Input
      value={email.value}
      onChange={email.onChange}
      onBlur={email.onBlur}
      error={email.error}
    />
  );
}
```

---

## When to Create a Custom Hook

**Create a hook when:**
- Same logic used in multiple components
- Complex logic you want to encapsulate
- You want to make logic testable

**Don't create a hook when:**
- Logic is simple and used once
- You'd just be wrapping one hook call
- It doesn't use any hooks inside

---

## Hook Composition Pattern

```tsx
// Low-level hook
function useTask(taskId) {
  return useQuery({ ... });
}

// Higher-level hook using useTask
function useArticleExtraction() {
  const [taskId, setTaskId] = useState(null);
  const task = useTask(taskId);

  const mutation = useMutation({
    mutationFn: extractArticle,
    onSuccess: (data) => setTaskId(data.task_id),
  });

  return {
    extract: mutation.mutate,
    isExtracting: mutation.isPending,
    task: task.data,
    isTaskRunning: isTaskRunning(task.data),
    isTaskComplete: isTaskComplete(task.data),
  };
}

// Component is simple
function ArticleExtractor() {
  const { extract, isExtracting, task, isTaskComplete } = useArticleExtraction();

  return (
    <div>
      <button onClick={() => extract({ url })}>Extract</button>
      {isExtracting && <p>Starting...</p>}
      {task && <TaskProgress task={task} />}
      {isTaskComplete && <p>Done!</p>}
    </div>
  );
}
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Custom hook** | Reusable logic with hooks |
| **use prefix** | Convention for hooks |
| **Encapsulation** | Hide complexity |
| **Composition** | Build complex from simple |
| **Return values** | Return what consumers need |

---

## Custom Hook Pattern

```tsx
// 1. Name starts with "use"
export function useMyHook(param) {
  // 2. Use other hooks
  const [state, setState] = useState();
  const query = useQuery({ ... });

  // 3. Add custom logic
  const computedValue = useMemo(() => ..., []);

  // 4. Return what consumers need
  return {
    state,
    setState,
    data: query.data,
    isLoading: query.isLoading,
    computedValue,
  };
}
```

---

## Try It Yourself

1. Open `frontend/src/hooks/useTask.ts`
2. Trace how it's used in components
3. Try creating a simple custom hook:
   ```tsx
   function useToggle(initial = false) {
     const [value, setValue] = useState(initial);
     const toggle = () => setValue(v => !v);
     return [value, toggle];
   }
   ```

---

## What's Next?

Hooks handle logic, but how do users navigate between pages? [Chapter 15: Routing with React Router](15-routing-with-react-router.md) explains single-page app navigation.

---

[← Previous: Mutations and Forms](13-mutations-and-forms.md) | [Back to Index](README.md) | [Next: Routing with React Router →](15-routing-with-react-router.md)
