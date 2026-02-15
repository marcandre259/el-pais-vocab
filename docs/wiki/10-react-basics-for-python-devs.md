# Chapter 10: React Basics for Python Devs

[← Previous: Middleware and CORS](09-middleware-and-cors.md) | [Back to Index](README.md) | [Next: TypeScript Essentials →](11-typescript-essentials.md)

---

## What is React?

React is a JavaScript library for building user interfaces. Key ideas:

- **Component-based**: UI is built from reusable pieces
- **Declarative**: Describe what you want, not how to do it
- **Virtual DOM**: Efficient updates by comparing changes

---

## Components as Functions

In React, a component is just a function that returns UI:

```tsx
// Python equivalent (conceptually)
def Greeting(name):
    return f"<h1>Hello, {name}!</h1>"

// React/JSX
function Greeting({ name }) {
  return <h1>Hello, {name}!</h1>;
}
```

**Components:**
- Start with capital letter (`Greeting`, not `greeting`)
- Return JSX (HTML-like syntax)
- Can be composed inside other components

---

## JSX: HTML-like Syntax in JavaScript

JSX lets you write HTML-like code that compiles to JavaScript:

```tsx
// This JSX:
const element = <h1 className="title">Hello</h1>;

// Compiles to:
const element = React.createElement('h1', { className: 'title' }, 'Hello');
```

**Key differences from HTML:**
- `className` instead of `class` (class is a reserved word in JS)
- `{}` for JavaScript expressions: `<span>{count}</span>`
- Self-closing tags must end with `/`: `<br />`, `<img />`

---

## Props: Passing Data to Components

Props (properties) are how you pass data into components:

```tsx
// Define a component that accepts props
interface GreetingProps {
  name: string;
  age?: number;  // Optional
}

function Greeting({ name, age }: GreetingProps) {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      {age && <p>Age: {age}</p>}
    </div>
  );
}

// Use the component
<Greeting name="Alice" age={30} />
<Greeting name="Bob" />  // age is optional
```

**Python comparison:**

```python
# Python function with kwargs
def greeting(name: str, age: int | None = None):
    result = f"Hello, {name}!"
    if age:
        result += f" Age: {age}"
    return result
```

---

## useState: Managing Component State

State is data that changes over time. `useState` creates state variables:

```tsx
import { useState } from 'react';

function Counter() {
  // useState returns [currentValue, setterFunction]
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}
```

**Key points:**
- `useState(0)` - Initial value is 0
- `count` - Current value
- `setCount` - Function to update the value
- When state changes, component re-renders

**Python comparison:**

```python
# Conceptually similar to:
class Counter:
    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    def set_count(self, value):
        self._count = value
        self.render()  # Re-render when changed
```

---

## Real Example: Button Component

From `frontend/src/components/ui/Button.tsx`:

```tsx
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className={styles.spinner} aria-hidden="true" />
      ) : null}
      <span className={loading ? styles.loadingText : ''}>{children}</span>
    </button>
  );
}
```

**Breaking it down:**

1. **Props interface** - Defines what the component accepts
   ```tsx
   interface ButtonProps {
     variant?: 'primary' | 'secondary';  // Optional, limited values
     loading?: boolean;  // Optional boolean
     children: ReactNode;  // Required, the button content
   }
   ```

2. **Destructuring with defaults**
   ```tsx
   function Button({
     variant = 'primary',  // Default value
     loading = false,
     children,
     ...props  // Rest of the props
   })
   ```

3. **Conditional rendering**
   ```tsx
   {loading ? <Spinner /> : null}  // Show spinner if loading
   ```

4. **Dynamic classes**
   ```tsx
   className={`${styles.button} ${styles[variant]}`}
   ```

---

## Thinking in Components

React encourages breaking UI into small, reusable pieces:

```
┌─────────────────────────────────────────────┐
│ App                                         │
│  ┌──────────────────────────────────────┐   │
│  │ Nav                                  │   │
│  │  ┌──────────┐  ┌──────────────────┐  │   │
│  │  │  Logo    │  │  NavLinks        │  │   │
│  │  └──────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Main                                 │   │
│  │  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ ArticleForm │  │ ThemeForm   │    │   │
│  │  └─────────────┘  └─────────────┘    │   │
│  │                                      │   │
│  │  ┌──────────────────────────────┐    │   │
│  │  │ TaskProgress                 │    │   │
│  │  └──────────────────────────────┘    │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Benefits:**
- Reusability: Use `Button` everywhere
- Isolation: Changes to `ArticleForm` don't affect `ThemeForm`
- Testing: Test each component independently

---

## Event Handling

Events in React use camelCase and pass functions:

```tsx
function Form() {
  const [text, setText] = useState('');

  // Event handler function
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();  // Stop form from reloading page
    console.log('Submitted:', text);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**Common events:**
- `onClick` - Mouse click
- `onChange` - Input value changed
- `onSubmit` - Form submitted
- `onKeyDown` - Key pressed

---

## Conditional Rendering

Several ways to conditionally render content:

```tsx
// 1. Ternary operator
{isLoading ? <Spinner /> : <Content />}

// 2. && short-circuit (renders nothing if false)
{error && <ErrorMessage error={error} />}

// 3. Null for nothing
{shouldShow ? <Thing /> : null}

// 4. Early return
function Component({ data }) {
  if (!data) return <Loading />;
  return <Display data={data} />;
}
```

---

## Lists and Keys

Rendering arrays requires a unique `key` prop:

```tsx
function WordList({ words }) {
  return (
    <ul>
      {words.map((word) => (
        <li key={word.id}>{word.lemma}: {word.translation}</li>
      ))}
    </ul>
  );
}
```

**Why keys matter:**
- React uses keys to track which items changed
- Keys should be stable, unique identifiers (like database IDs)
- Don't use array index if items can be reordered

---

## Comparison: Python vs React Patterns

| Python | React |
|--------|-------|
| `class` | `function` component |
| `self.state = {}` | `useState()` |
| `def render(self)` | Return JSX from function |
| Template strings | JSX with `{}` expressions |
| Inheritance | Composition (components inside components) |
| Decorators | Higher-order components / hooks |

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Component** | Reusable UI building block |
| **JSX** | HTML-like syntax in JavaScript |
| **Props** | Data passed into components |
| **useState** | Component state that triggers re-renders |
| **Events** | User interactions (onClick, onChange) |
| **Conditional rendering** | Show/hide based on conditions |

---

## Try It Yourself

1. Open `frontend/src/components/ui/Button.tsx`
2. Trace how props flow from usage to rendering
3. Try changing the `variant` prop and see the visual change
4. Add a new prop (like `fullWidth`) and use it in the styles

---

## What's Next?

You may have noticed the `: string` and `interface` syntax. [Chapter 11: TypeScript Essentials](11-typescript-essentials.md) explains how TypeScript adds types to JavaScript to catch bugs early.

---

[← Previous: Middleware and CORS](09-middleware-and-cors.md) | [Back to Index](README.md) | [Next: TypeScript Essentials →](11-typescript-essentials.md)
