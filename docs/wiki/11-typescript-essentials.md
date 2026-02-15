# Chapter 11: TypeScript Essentials

[← Previous: React Basics for Python Devs](10-react-basics-for-python-devs.md) | [Back to Index](README.md) | [Next: Fetching Data with React Query →](12-fetching-data-with-react-query.md)

---

## Why Types?

JavaScript is dynamically typed - you can put anything anywhere:

```javascript
let x = 5;
x = "hello";  // Fine in JavaScript
x.toUpperCase();  // Works
x = 5;
x.toUpperCase();  // Runtime error! 5 has no toUpperCase
```

TypeScript catches these errors before you run the code:

```typescript
let x: number = 5;
x = "hello";  // Error: Type 'string' is not assignable to type 'number'
```

**Python comparison:** Like Python type hints, but enforced by the compiler.

---

## Basic Types

```typescript
// Primitives
let name: string = "Alice";
let age: number = 30;
let active: boolean = true;

// Arrays
let numbers: number[] = [1, 2, 3];
let names: string[] = ["Alice", "Bob"];

// Objects
let person: { name: string; age: number } = {
  name: "Alice",
  age: 30
};

// Any (escape hatch - avoid when possible)
let data: any = "could be anything";

// Unknown (safer than any)
let input: unknown = getUserInput();
```

**Python comparison:**

```python
name: str = "Alice"
age: int = 30
numbers: list[int] = [1, 2, 3]
```

---

## Interfaces

Interfaces define the shape of objects:

```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

function greet(user: User) {
  console.log(`Hello, ${user.name}`);
}

// This works
greet({ id: 1, name: "Alice", email: "alice@example.com" });

// This fails - missing email
greet({ id: 1, name: "Alice" });
// Error: Property 'email' is missing
```

---

## Real Example: API Types

From `frontend/src/api/types.ts`:

```typescript
// Task types
export type TaskType = 'article_extract' | 'theme_create' | 'audio_generate' | 'anki_sync';
export type TaskStatusEnum = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface TaskStatus {
  task_id: string;
  type: TaskType;
  status: TaskStatusEnum;
  progress?: string;        // Optional
  result?: unknown;         // Optional, any type
  error?: string;           // Optional
  created_at: string;
  completed_at?: string;    // Optional
}
```

**Key patterns:**

1. **Type aliases for string unions**
   ```typescript
   type TaskType = 'article_extract' | 'theme_create';
   // Can only be one of these exact strings
   ```

2. **Optional properties with `?`**
   ```typescript
   progress?: string;  // Can be string or undefined
   ```

3. **Unknown for flexible types**
   ```typescript
   result?: unknown;  // We don't know the exact shape
   ```

---

## Vocabulary Types

```typescript
export interface VocabularyWord {
  id: number;
  word: string;
  lemma: string;
  pos?: string;               // Part of speech, optional
  gender?: string;            // Optional
  translation: string;
  source_lang?: string;
  target_lang?: string;
  examples: string[];         // Array of strings
  source?: string;
  theme: string;
  added_at?: string;
}
```

**Python equivalent (Pydantic):**

```python
class VocabularyWord(BaseModel):
    id: int
    word: str
    lemma: str
    pos: Optional[str] = None
    gender: Optional[str] = None
    translation: str
    examples: list[str] = []
    theme: str
```

**Notice:** TypeScript interfaces match our Pydantic models - this ensures frontend and backend agree on data shapes.

---

## Generic Types

Generics let you create reusable types with placeholders:

```typescript
// Generic interface
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Usage - T becomes VocabularyWord
const response: PaginatedResponse<VocabularyWord> = {
  items: [{ id: 1, word: "casa", ... }],
  total: 100,
  page: 1,
  page_size: 10,
  total_pages: 10
};

// Or with Theme
const themes: PaginatedResponse<Theme> = { ... };
```

**Python comparison:**

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
```

---

## Record Type

`Record` creates an object type with specific key and value types:

```typescript
// Object with string keys and number values
interface VocabularyStats {
  total_words: number;
  by_pos: Record<string, number>;   // { "noun": 50, "verb": 30, ... }
  by_theme: Record<string, number>; // { "el_pais": 100, "kitchen": 20, ... }
}
```

**Python comparison:**

```python
by_pos: dict[str, int]
```

---

## Union Types

A value can be one of several types:

```typescript
// String or undefined
let name: string | undefined = undefined;

// Specific string values
type Status = 'pending' | 'completed' | 'failed';

// Different object types
type Response = SuccessResponse | ErrorResponse;
```

---

## Type Inference

TypeScript can often figure out types automatically:

```typescript
// Type is inferred as number
let x = 5;

// Type is inferred as string[]
let names = ["Alice", "Bob"];

// Type is inferred from function return
function double(n: number) {
  return n * 2;  // Return type inferred as number
}
```

**When to explicitly type:**
- Function parameters (always)
- Complex objects where inference is unclear
- Public API boundaries

---

## Function Types

```typescript
// Function with typed parameters and return
function add(a: number, b: number): number {
  return a + b;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Function type as a variable
type MathOp = (a: number, b: number) => number;
const divide: MathOp = (a, b) => a / b;

// Async function
async function fetchUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

---

## Using Types with React

```typescript
// Props interface
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  onClick: () => void;          // Function that takes nothing, returns nothing
  children: React.ReactNode;    // Any valid React children
}

// Component with typed props
function Button({ variant = 'primary', onClick, children }: ButtonProps) {
  return (
    <button className={variant} onClick={onClick}>
      {children}
    </button>
  );
}

// Usage - TypeScript checks props
<Button variant="primary" onClick={() => console.log('clicked')}>
  Click me
</Button>

// Error: 'invalid' is not assignable to 'primary' | 'secondary'
<Button variant="invalid">Click me</Button>
```

---

## Common React Types

```typescript
import type { ReactNode, FormEvent, ChangeEvent } from 'react';

// Children of a component
children: ReactNode;

// Form submit event
const handleSubmit = (e: FormEvent) => {
  e.preventDefault();
};

// Input change event
const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};

// Select change event
const handleSelect = (e: ChangeEvent<HTMLSelectElement>) => {
  setSelected(e.target.value);
};
```

---

## Type Assertions

Sometimes you know more than TypeScript:

```typescript
// You know this is a specific type
const data = JSON.parse(text) as User;

// For HTML elements
const input = document.getElementById('myInput') as HTMLInputElement;
input.value = 'hello';
```

**Use sparingly** - prefer letting TypeScript infer types.

---

## Benefits Over Plain JavaScript

1. **Catch errors early** - Before running the code
2. **Better autocomplete** - IDE knows what properties exist
3. **Self-documenting** - Types explain what functions expect
4. **Refactoring safety** - Change a type, find all affected code

---

## Summary

| Concept | Example | Purpose |
|---------|---------|---------|
| **Basic types** | `string`, `number`, `boolean` | Primitive values |
| **Arrays** | `string[]` | List of same type |
| **Interfaces** | `interface User { ... }` | Object shapes |
| **Optional** | `name?: string` | May be undefined |
| **Union** | `'a' \| 'b'` | One of several types |
| **Generic** | `Array<T>` | Reusable type with placeholder |
| **Record** | `Record<string, number>` | Object with typed keys/values |

---

## Try It Yourself

1. Open `frontend/src/api/types.ts`
2. Compare `TaskStatus` interface to the Python `TaskStatus` Pydantic model
3. Try adding a new field to both - notice how TypeScript catches mismatches
4. Hover over variables in VS Code to see their inferred types

---

## What's Next?

Now that you understand types, [Chapter 12: Fetching Data with React Query](12-fetching-data-with-react-query.md) shows how to fetch typed data from the API and manage server state.

---

[← Previous: React Basics for Python Devs](10-react-basics-for-python-devs.md) | [Back to Index](README.md) | [Next: Fetching Data with React Query →](12-fetching-data-with-react-query.md)
