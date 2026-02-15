# Chapter 2: How Web Apps Work

[← Previous: Project Overview](01-project-overview.md) | [Back to Index](README.md) | [Next: FastAPI Basics →](03-fastapi-basics.md)

---

## The Client-Server Model

At its core, a web application is a conversation between two parties:

```
┌──────────────┐         Request         ┌──────────────┐
│              │ ──────────────────────► │              │
│    Client    │                         │    Server    │
│  (Frontend)  │ ◄────────────────────── │  (Backend)   │
│              │         Response        │              │
└──────────────┘                         └──────────────┘
```

**Client**: The browser (or any program) that initiates requests. It asks for things.

**Server**: The program that listens for requests and sends responses. It provides things.

**Key insight**: The client and server are independent programs. They could be on the same computer (during development) or thousands of miles apart (in production). They communicate through a shared language: HTTP.

---

## HTTP: The Language of the Web

HTTP (HyperText Transfer Protocol) is how clients and servers talk. Every request has:

### 1. A Method (What You Want to Do)

| Method | Purpose | Example |
|--------|---------|---------|
| `GET` | Retrieve data | Get list of words |
| `POST` | Create something new | Add a new word |
| `PUT` | Update (replace) | Update a word's translation |
| `PATCH` | Update (partial) | Change just one field |
| `DELETE` | Remove something | Delete a word |

### 2. A URL (Where to Do It)

```
http://localhost:8000/api/vocabulary?page=1&limit=10
└─┬─┘ └─────┬─────┘ └──────┬──────┘ └──────┬──────┘
protocol    host         path         query params
```

### 3. Headers (Metadata)

```
Content-Type: application/json
Authorization: Bearer token123
```

### 4. Body (The Data)

For `POST`/`PUT`/`PATCH`, the actual data you're sending:

```json
{
  "lemma": "casa",
  "translation": "maison"
}
```

---

## A Request-Response Example

Let's trace a real request in our app - fetching vocabulary words:

### The Request

```http
GET /api/vocabulary?page=1&limit=10 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### The Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": 1,
      "lemma": "casa",
      "translation": "maison",
      "examples": ["La casa es grande"]
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 10
}
```

### Response Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | OK | Request succeeded |
| `201` | Created | New resource created (POST success) |
| `204` | No Content | Success, nothing to return (DELETE) |
| `400` | Bad Request | Invalid input from client |
| `404` | Not Found | Resource doesn't exist |
| `422` | Unprocessable Entity | Validation failed |
| `500` | Server Error | Something broke on the server |

---

## JSON: The Data Format

JSON (JavaScript Object Notation) is how we structure data in requests and responses:

```json
{
  "string": "hello",
  "number": 42,
  "boolean": true,
  "null": null,
  "array": [1, 2, 3],
  "object": {
    "nested": "value"
  }
}
```

**Why JSON?**
- Human-readable
- Language-agnostic (Python, JavaScript, etc. all support it)
- Maps naturally to programming data structures

**Python dict ↔ JSON mapping:**

```python
# Python
data = {
    "lemma": "casa",
    "examples": ["La casa es grande"]
}

# JSON (identical syntax)
{
  "lemma": "casa",
  "examples": ["La casa es grande"]
}
```

---

## How the Frontend Talks to the Backend

In our app, the React frontend makes HTTP requests to the FastAPI backend:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    React App                             │   │
│  │                                                          │   │
│  │   User clicks "Load Words"                               │   │
│  │           │                                              │   │
│  │           ▼                                              │   │
│  │   fetch('/api/vocabulary')  ─────────────────────────────┼───┼──►
│  │           │                                              │   │
│  │           │ (waits for response)                         │   │
│  │           │                                              │   │
│  │   ◄───────┼──────────────────────────────────────────────┼───┼───
│  │           ▼                                              │   │
│  │   Display words in UI                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Request
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Server                               │
│                                                                 │
│   Receive request at /api/vocabulary                            │
│           │                                                     │
│           ▼                                                     │
│   Query database                                                │
│           │                                                     │
│           ▼                                                     │
│   Return JSON response                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Proxy Setup (Development)

During development, we have two servers:
- Frontend dev server: `http://localhost:5173`
- Backend API server: `http://localhost:8000`

**The problem**: Browsers have security rules (CORS) that restrict requests to different origins.

**The solution**: A proxy. The frontend dev server forwards API requests to the backend:

```
Browser                Frontend Server           Backend Server
(localhost:5173)       (localhost:5173)          (localhost:8000)
       │                      │                         │
       │  /api/vocabulary     │                         │
       │─────────────────────►│                         │
       │                      │  /api/vocabulary        │
       │                      │────────────────────────►│
       │                      │                         │
       │                      │◄────────────────────────│
       │◄─────────────────────│                         │
       │                      │                         │
```

This is configured in `frontend/vite.config.ts`:

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
})
```

**Key insight**: The browser thinks it's talking to `localhost:5173` for everything. The proxy transparently forwards `/api/*` requests to the backend.

---

## Synchronous vs Asynchronous Requests

### Synchronous (Blocking)

```
Request ────────────────────────────────► Response
        (nothing else happens while waiting)
```

### Asynchronous (Non-Blocking)

```
Request ────────────────────────────────► Response
    │                                        │
    └── UI remains responsive ───────────────┘
        User can interact, see loading spinner
```

Web apps use **asynchronous** requests so the UI stays responsive. In JavaScript:

```typescript
// Async/await syntax
const response = await fetch('/api/vocabulary');
const data = await response.json();
// Code here runs AFTER the response arrives
```

---

## REST API Conventions

Our API follows REST (Representational State Transfer) conventions:

### Resource-Based URLs

```
/api/vocabulary          # Collection of words
/api/vocabulary/123      # Single word (id=123)
/api/themes              # Collection of themes
/api/themes/kitchen      # Single theme
```

### Method Meanings

```
GET    /api/vocabulary       # List all words
POST   /api/vocabulary       # Create a word
GET    /api/vocabulary/123   # Get word 123
PUT    /api/vocabulary/123   # Replace word 123
DELETE /api/vocabulary/123   # Delete word 123
```

### Consistent Response Format

Our API returns consistent structures:

```json
// List response (paginated)
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 10
}

// Single item response
{
  "id": 123,
  "lemma": "casa",
  ...
}

// Error response
{
  "detail": "Word not found"
}
```

---

## Real Code: Making a Request

From `frontend/src/api/client.ts`:

```typescript
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(endpoint, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      error.detail || 'Request failed',
      response.status
    );
  }

  return response.json();
}
```

**What this does:**
1. Makes an HTTP request with JSON headers
2. Checks if response was successful (`response.ok`)
3. Throws an error with details if it failed
4. Returns parsed JSON if successful

---

## Summary

| Concept | Description |
|---------|-------------|
| **Client-Server** | Browser asks, server answers |
| **HTTP Methods** | GET (read), POST (create), DELETE (remove), etc. |
| **URLs** | Identify what resource you're accessing |
| **JSON** | Data format for request/response bodies |
| **Status Codes** | Numbers indicating success (200s) or failure (400s, 500s) |
| **Async Requests** | Non-blocking - UI stays responsive |
| **Proxy** | Development trick to avoid CORS issues |

---

## Try It Yourself

1. Open browser dev tools (F12) → Network tab
2. Visit the frontend and click around
3. Watch the HTTP requests appear - note the method, URL, and response

Or use `curl` from the terminal:

```bash
# Get vocabulary
curl http://localhost:8000/api/vocabulary

# Get single word
curl http://localhost:8000/api/vocabulary/1

# Create a word (POST with JSON body)
curl -X POST http://localhost:8000/api/vocabulary \
  -H "Content-Type: application/json" \
  -d '{"lemma": "test", "translation": "teste"}'
```

---

## What's Next?

Now that you understand how clients and servers communicate, let's build a server! [Chapter 3: FastAPI Basics](03-fastapi-basics.md) shows how to create endpoints that handle these HTTP requests.

---

[← Previous: Project Overview](01-project-overview.md) | [Back to Index](README.md) | [Next: FastAPI Basics →](03-fastapi-basics.md)
