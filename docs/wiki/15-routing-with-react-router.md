# Chapter 15: Routing with React Router

[← Previous: Custom Hooks](14-custom-hooks.md) | [Back to Index](README.md) | [Next: Styling with CSS →](16-styling-with-css.md)

---

## What is a Single Page App (SPA)?

Traditional websites load a new HTML page for each URL:

```
Click link → Server sends new HTML → Browser renders entire page
```

Single Page Apps load once, then update dynamically:

```
Click link → JavaScript updates URL → React renders new component
```

**Benefits:**
- Faster navigation (no full page reload)
- Smooth transitions
- Maintains app state between pages

---

## React Router Basics

React Router maps URLs to components:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/browse" element={<Browse />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}
```

**What happens:**
- URL is `/` → Render `<Home />`
- URL is `/browse` → Render `<Browse />`
- URL is `/settings` → Render `<Settings />`

---

## Real Example: App.tsx

From `frontend/src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Home } from './pages/Home';
import { Browse } from './pages/Browse';
import styles from './App.module.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className={styles.app}>
          <nav className={styles.nav}>
            <div className={styles.navContent}>
              <span className={styles.logo}>El Pais Vocab</span>
              <div className={styles.navLinks}>
                <NavLink
                  to="/"
                  end
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.active : ''}`
                  }
                >
                  Capture
                </NavLink>
                <NavLink
                  to="/browse"
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.active : ''}`
                  }
                >
                  Browse
                </NavLink>
              </div>
            </div>
          </nav>

          <main className={styles.main}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/browse" element={<Browse />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## Key Components

### BrowserRouter

Wraps your app to enable routing:

```tsx
<BrowserRouter>
  {/* Your app */}
</BrowserRouter>
```

Uses the browser's history API for clean URLs like `/browse` (not `/#/browse`).

### Routes and Route

Define the URL → component mapping:

```tsx
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/browse" element={<Browse />} />
</Routes>
```

- `path` - URL pattern to match
- `element` - Component to render

### NavLink

Navigation links that know if they're active:

```tsx
<NavLink
  to="/browse"
  className={({ isActive }) =>
    isActive ? 'nav-link active' : 'nav-link'
  }
>
  Browse
</NavLink>
```

**vs regular `<a>` tag:**
- `<a href="/browse">` - Full page reload
- `<NavLink to="/browse">` - SPA navigation, no reload

### The `end` prop

For the root path, use `end` to only match exactly `/`:

```tsx
<NavLink to="/" end>Home</NavLink>
```

Without `end`, `/browse` would also match `/` because all paths start with `/`.

---

## Navigation Patterns

### Declarative (Links)

```tsx
import { Link, NavLink } from 'react-router-dom';

// Simple link
<Link to="/browse">Go to Browse</Link>

// NavLink with active state
<NavLink
  to="/browse"
  className={({ isActive }) => isActive ? 'active' : ''}
>
  Browse
</NavLink>
```

### Programmatic (useNavigate)

```tsx
import { useNavigate } from 'react-router-dom';

function LoginForm() {
  const navigate = useNavigate();

  const handleLogin = async () => {
    await login();
    navigate('/dashboard');  // Redirect after login
  };

  return <button onClick={handleLogin}>Login</button>;
}
```

---

## URL Parameters

Capture parts of the URL:

```tsx
// Route definition
<Route path="/words/:wordId" element={<WordDetail />} />

// Component using the parameter
import { useParams } from 'react-router-dom';

function WordDetail() {
  const { wordId } = useParams();  // Extract from URL
  // URL: /words/123 → wordId = "123"

  return <div>Word ID: {wordId}</div>;
}
```

---

## Layout Pattern

Shared layout with nested routes:

```tsx
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function Layout() {
  return (
    <div>
      <nav>
        <NavLink to="/">Home</NavLink>
        <NavLink to="/browse">Browse</NavLink>
      </nav>

      <main>
        <Outlet />  {/* Child routes render here */}
      </main>
    </div>
  );
}
```

---

## Active Link Styling

From our app:

```tsx
<NavLink
  to="/browse"
  className={({ isActive }) =>
    `${styles.navLink} ${isActive ? styles.active : ''}`
  }
>
  Browse
</NavLink>
```

The `className` function receives `{ isActive }` and can return different classes.

CSS:

```css
.navLink {
  color: gray;
}

.navLink.active {
  color: blue;
  font-weight: bold;
}
```

---

## 404 Not Found

Handle unknown routes:

```tsx
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/browse" element={<Browse />} />
  <Route path="*" element={<NotFound />} />  {/* Catch all */}
</Routes>

function NotFound() {
  return <h1>Page not found</h1>;
}
```

---

## Query Parameters

Access URL query parameters:

```tsx
import { useSearchParams } from 'react-router-dom';

function Browse() {
  const [searchParams, setSearchParams] = useSearchParams();

  const page = searchParams.get('page') || '1';
  // URL: /browse?page=2 → page = "2"

  const goToPage = (num) => {
    setSearchParams({ page: String(num) });
    // Updates URL to /browse?page=3
  };

  return (
    <div>
      <p>Page {page}</p>
      <button onClick={() => goToPage(Number(page) + 1)}>Next</button>
    </div>
  );
}
```

---

## Summary

| Component | Purpose |
|-----------|---------|
| `BrowserRouter` | Enable routing in app |
| `Routes` | Container for route definitions |
| `Route` | Map path to component |
| `Link` | Navigation without reload |
| `NavLink` | Link with active state |
| `useNavigate` | Programmatic navigation |
| `useParams` | Access URL parameters |
| `useSearchParams` | Access query parameters |

---

## Route Structure in Our App

```
/           → Home (Capture page)
/browse     → Browse (Vocabulary list)
```

```tsx
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/browse" element={<Browse />} />
</Routes>
```

---

## Try It Yourself

1. Open the app and watch the URL change as you navigate
2. Notice the page doesn't fully reload
3. Try adding a new route for `/settings`
4. Use browser back/forward - they work correctly

---

## What's Next?

We've been importing CSS modules throughout. [Chapter 16: Styling with CSS](16-styling-with-css.md) explains how CSS modules work and why we use them.

---

[← Previous: Custom Hooks](14-custom-hooks.md) | [Back to Index](README.md) | [Next: Styling with CSS →](16-styling-with-css.md)
