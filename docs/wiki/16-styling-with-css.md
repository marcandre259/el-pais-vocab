# Chapter 16: Styling with CSS

[← Previous: Routing with React Router](15-routing-with-react-router.md) | [Back to Index](README.md) | [Next: The API Client Pattern →](17-the-api-client-pattern.md)

---

## The Problem with Global CSS

Traditional CSS is global - any style can affect any element:

```css
/* styles.css */
.button {
  background: blue;
}
```

```html
<!-- Any button in any component gets this style -->
<button class="button">Click me</button>
```

**Problems:**
- Name collisions (two components both use `.button`)
- Unexpected style changes
- Hard to delete unused CSS
- Difficult to reason about

---

## CSS Modules: Scoped Styles

CSS Modules automatically scope styles to the component:

```css
/* Button.module.css */
.button {
  background: blue;
  padding: 10px;
}
```

```tsx
// Button.tsx
import styles from './Button.module.css';

function Button() {
  return <button className={styles.button}>Click me</button>;
}
```

**What happens:**
- `.button` becomes `.Button_button_a1b2c3` (unique hash)
- Only this component gets this style
- No collisions possible

---

## Real Example: Button Styles

From `frontend/src/components/ui/Button.module.css`:

```css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

/* Variants */
.primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.ghost {
  background: transparent;
  color: var(--color-text);
  border: none;
}

/* Sizes */
.sm { padding: 0.5rem 1rem; font-size: 0.875rem; }
.md { padding: 0.75rem 1.5rem; font-size: 1rem; }
.lg { padding: 1rem 2rem; font-size: 1.125rem; }
```

Usage in component:

```tsx
import styles from './Button.module.css';

function Button({ variant = 'primary', size = 'md', className = '', ...props }) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className}`}
      {...props}
    />
  );
}
```

---

## Dynamic Class Names

Combine multiple classes:

```tsx
// String interpolation
className={`${styles.button} ${styles[variant]} ${styles[size]}`}

// Conditional classes
className={`${styles.button} ${isActive ? styles.active : ''}`}

// Multiple conditionals
className={[
  styles.button,
  styles[variant],
  isActive && styles.active,
  isDisabled && styles.disabled,
].filter(Boolean).join(' ')}
```

---

## CSS Variables (Custom Properties)

CSS variables let you define reusable values:

From `frontend/src/index.css`:

```css
:root {
  /* Colors */
  --color-primary: #0066cc;
  --color-primary-dark: #0052a3;
  --color-text: #1a1a1a;
  --color-text-muted: #666666;
  --color-background: #ffffff;
  --color-border: #e5e5e5;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;

  /* Typography */
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;

  /* Borders */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

Using variables:

```css
.card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
}
```

**Benefits:**
- Consistent design system
- Easy theme changes
- Dark mode support (redefine variables)

---

## Component-Specific Styles

Each component has its own CSS module:

```
components/
├── ui/
│   ├── Button.tsx
│   ├── Button.module.css
│   ├── Input.tsx
│   ├── Input.module.css
│   ├── Card.tsx
│   └── Card.module.css
├── ArticleForm.tsx
├── ArticleForm.module.css
├── WordList.tsx
└── WordList.module.css
```

---

## Global Styles

Some styles should be global (resets, variables, base typography):

```css
/* index.css - global styles */
*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--color-text);
  background: var(--color-background);
}
```

Import in entry point:

```tsx
// main.tsx
import './index.css';
```

---

## Composing Styles

Combine base styles with component styles:

```css
/* Card.module.css */
.card {
  background: var(--color-background);
  border-radius: var(--radius-md);
}

.elevated {
  composes: card;  /* Includes .card styles */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.flat {
  composes: card;
  border: 1px solid var(--color-border);
}
```

Usage:

```tsx
<div className={styles.elevated}>
  {/* Has both .card and .elevated styles */}
</div>
```

---

## Responsive Design

Use media queries for different screen sizes:

```css
.container {
  padding: var(--spacing-md);
}

@media (min-width: 768px) {
  .container {
    padding: var(--spacing-lg);
    max-width: 1200px;
    margin: 0 auto;
  }
}

.grid {
  display: grid;
  gap: var(--spacing-md);
  grid-template-columns: 1fr;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## Loading States

```css
.spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loadingText {
  opacity: 0.7;
}
```

---

## Hover and Focus States

```css
.button {
  background: var(--color-primary);
  transition: all 0.15s ease;
}

.button:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
}

.button:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.3);
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## Summary

| Concept | Purpose |
|---------|---------|
| **CSS Modules** | Scoped styles, no collisions |
| **CSS Variables** | Reusable values, theming |
| **Global CSS** | Base styles, resets |
| **Media queries** | Responsive design |
| **Transitions** | Smooth state changes |

---

## File Naming Convention

```
ComponentName.tsx         # Component
ComponentName.module.css  # Scoped styles for that component
```

The `.module.css` extension tells the bundler to process it as a CSS Module.

---

## Try It Yourself

1. Open a component and its CSS module
2. Inspect elements in browser dev tools - see the generated class names
3. Try changing a CSS variable in `:root` and watch it cascade
4. Add a hover effect to a component

---

## What's Next?

That completes the frontend section! [Chapter 17: The API Client Pattern](17-the-api-client-pattern.md) shows how frontend and backend connect through a centralized API client.

---

[← Previous: Routing with React Router](15-routing-with-react-router.md) | [Back to Index](README.md) | [Next: The API Client Pattern →](17-the-api-client-pattern.md)
