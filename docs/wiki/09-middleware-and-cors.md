# Chapter 9: Middleware and CORS

[← Previous: Configuration and Settings](08-configuration-and-settings.md) | [Back to Index](README.md) | [Next: React Basics for Python Devs →](10-react-basics-for-python-devs.md)

---

## What is Middleware?

Middleware is code that runs on every request, before and after your route handlers:

```
Request → [Middleware 1] → [Middleware 2] → [Route Handler]
                                                   ↓
Response ← [Middleware 1] ← [Middleware 2] ← [Response]
```

**Common uses:**
- Logging all requests
- Authentication/authorization
- CORS headers (cross-origin requests)
- Request timing
- Error handling

---

## Middleware in FastAPI

From `api/app.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings

app = FastAPI(...)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Order matters:** Middleware is processed in reverse order of how you add it. The first middleware added is the outermost layer.

---

## What is CORS?

**CORS** (Cross-Origin Resource Sharing) is a browser security feature.

**The same-origin policy:**

Browsers block requests from one origin to another by default:

```
Frontend: http://localhost:3000
Backend:  http://localhost:8000

These are DIFFERENT ORIGINS (different ports)
Browser blocks the request by default!
```

**Origin = protocol + domain + port**

| URL | Origin |
|-----|--------|
| `http://localhost:3000` | `http://localhost:3000` |
| `http://localhost:8000` | `http://localhost:8000` |
| `https://example.com` | `https://example.com` |
| `https://api.example.com` | `https://api.example.com` |

---

## Why CORS Exists

Without CORS, a malicious website could:

```javascript
// On evil.com
fetch('https://yourbank.com/api/transfer', {
  method: 'POST',
  credentials: 'include',  // Send user's bank cookies!
  body: JSON.stringify({to: 'hacker', amount: 10000})
});
```

CORS prevents this by requiring servers to explicitly allow cross-origin requests.

---

## How CORS Works

**Step 1: Preflight Request**

For "complex" requests (POST with JSON, custom headers), the browser sends an OPTIONS request first:

```http
OPTIONS /api/vocabulary HTTP/1.1
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

**Step 2: Server Response**

The server indicates what's allowed:

```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, DELETE
Access-Control-Allow-Headers: content-type
```

**Step 3: Actual Request**

If preflight passes, browser sends the real request:

```http
POST /api/vocabulary HTTP/1.1
Origin: http://localhost:3000
Content-Type: application/json
```

---

## CORS Configuration

From `api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Which origins can access
    allow_credentials=True,               # Allow cookies
    allow_methods=["*"],                  # Allow all HTTP methods
    allow_headers=["*"],                  # Allow all headers
)
```

**Configuration options:**

| Option | Purpose | Example |
|--------|---------|---------|
| `allow_origins` | Allowed origins | `["http://localhost:3000"]` |
| `allow_credentials` | Allow cookies | `True` |
| `allow_methods` | Allowed HTTP methods | `["GET", "POST"]` or `["*"]` |
| `allow_headers` | Allowed headers | `["Authorization"]` or `["*"]` |

---

## Development vs Production CORS

**Development (permissive):**

```python
cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:3000",
]
```

**Production (restrictive):**

```python
cors_origins = [
    "https://myapp.com",
    "https://www.myapp.com",
]
```

**Never use `allow_origins=["*"]` with `allow_credentials=True`** - this is a security risk.

---

## The Proxy Alternative

During development, you can avoid CORS entirely with a proxy:

```
Browser → Frontend Server (localhost:3000) → Backend (localhost:8000)
          └── Proxy forwards /api/* requests
```

The browser only talks to one origin (localhost:3000), so CORS doesn't apply.

In `frontend/vite.config.ts`:

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

**Pros:** No CORS configuration needed during development
**Cons:** Only works with dev server, need CORS for production

---

## Custom Middleware Example

Here's how you'd write custom middleware:

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    # BEFORE the request is processed
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # AFTER the request is processed
    duration = time.time() - start_time
    response.headers["X-Process-Time"] = str(duration)

    return response
```

**What happens:**
1. Request comes in
2. `start_time` is recorded
3. `call_next(request)` passes to the next middleware/route
4. Response comes back
5. Duration is calculated and added to headers
6. Response is returned

---

## Common Middleware Patterns

### Logging Middleware

```python
import logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Status: {response.status_code}")
    return response
```

### Authentication Middleware

```python
@app.middleware("http")
async def check_auth(request: Request, call_next):
    # Skip auth for certain paths
    if request.url.path in ["/health", "/docs"]:
        return await call_next(request)

    # Check for auth header
    auth = request.headers.get("Authorization")
    if not auth:
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"}
        )

    return await call_next(request)
```

---

## Middleware vs Dependencies

FastAPI has two ways to run code on requests:

**Middleware:** Runs on EVERY request

```python
@app.middleware("http")
async def my_middleware(request, call_next):
    # Runs on every single request
    ...
```

**Dependencies:** Runs on specific routes

```python
def verify_token(token: str = Header(...)):
    # Only runs on routes that use this dependency
    ...

@router.get("/protected", dependencies=[Depends(verify_token)])
def protected_route():
    ...
```

**Use middleware for:** Logging, timing, CORS, request ID
**Use dependencies for:** Authentication, authorization, resource loading

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Middleware** | Code that runs on every request |
| **CORS** | Browser security for cross-origin requests |
| **Origins** | Protocol + domain + port |
| **Preflight** | OPTIONS request to check permissions |
| **allow_origins** | Which origins can access the API |
| **Proxy** | Development alternative to CORS |

---

## CORS Troubleshooting

**Error:** "has been blocked by CORS policy"

**Solutions:**
1. Check `allow_origins` includes your frontend URL
2. Check the origin exactly (http vs https, port numbers)
3. Restart the backend after changing config
4. Check browser console for the specific origin being blocked

**Debugging tip:** Look at the Network tab in browser dev tools. The preflight OPTIONS request will show what headers the server returns.

---

## Try It Yourself

1. Open browser dev tools → Network tab
2. Make an API request from the frontend
3. Look for the preflight OPTIONS request
4. Examine the CORS headers in the response

Or test CORS manually:

```bash
# This should work (matching origin)
curl -H "Origin: http://localhost:3000" \
     -I http://localhost:8000/api/vocabulary

# Look for Access-Control-Allow-Origin in response
```

---

## What's Next?

That completes the backend section! [Chapter 10: React Basics for Python Devs](10-react-basics-for-python-devs.md) starts the frontend section, introducing React concepts for developers coming from Python.

---

[← Previous: Configuration and Settings](08-configuration-and-settings.md) | [Back to Index](README.md) | [Next: React Basics for Python Devs →](10-react-basics-for-python-devs.md)
