# Appendix A: Glossary

[← Previous: Testing with pytest](21-testing-with-pytest.md) | [Back to Index](README.md) | [Next: Common Patterns →](appendix-b-common-patterns.md)

---

Quick definitions of terms used throughout this guide.

## A

**API (Application Programming Interface)**
A set of rules for how software components communicate. In this project, the REST API lets the frontend talk to the backend.

**async/await**
Python syntax for asynchronous programming. `async def` defines a coroutine; `await` pauses until an operation completes.

**AUTOINCREMENT**
SQLite keyword that automatically assigns the next available integer to a column.

## B

**Background Task**
An operation that runs separately from the main request, allowing the server to respond immediately while work continues.

**BaseModel**
Pydantic class that all data models inherit from. Provides validation, serialization, and type checking.

**BaseSettings**
Pydantic class for configuration management. Automatically loads values from environment variables.

## C

**Component**
In React, a reusable piece of UI defined as a function that returns JSX.

**CORS (Cross-Origin Resource Sharing)**
Browser security feature that controls which origins can access an API.

**CRUD**
Create, Read, Update, Delete - the four basic database operations.

**CSS Modules**
A CSS file where class names are scoped to the component, preventing style conflicts.

## D

**Decorator**
In Python, a function that wraps another function. In FastAPI, `@app.get("/")` decorates route handlers.

## E

**Endpoint**
A specific URL path that accepts requests, like `/api/vocabulary`.

**Environment Variable**
A variable set outside the code, used for configuration. Accessed via `os.getenv()` or Pydantic Settings.

## F

**FastAPI**
A modern Python web framework for building APIs with automatic validation and documentation.

**Fixture**
In pytest, a function that provides setup/teardown for tests.

**Foreign Key**
A database column that references another table's primary key.

## G

**Generic Type**
A type that works with multiple types, like `List[T]` where `T` can be any type.

## H

**Hook**
In React, a function that lets you use React features in function components. Examples: `useState`, `useQuery`.

**HTTP (HyperText Transfer Protocol)**
The protocol for communication between clients and servers on the web.

## I

**Interface**
In TypeScript, defines the shape of an object - what properties it has and their types.

**Immutable**
Cannot be changed after creation. Pydantic models are immutable by default.

## J

**JSON (JavaScript Object Notation)**
A text format for structured data, used for API communication.

**JSX**
JavaScript XML - syntax that lets you write HTML-like code in JavaScript/React.

## M

**Middleware**
Code that runs on every request, before and after route handlers.

**Migration**
A change to database schema (adding/removing tables or columns).

**Mutation**
In React Query, an operation that changes data (POST, PUT, DELETE).

## O

**Origin**
In web security, the combination of protocol + domain + port (e.g., `http://localhost:3000`).

## P

**Pagination**
Splitting large result sets into pages (page 1, page 2, etc.).

**Path Parameter**
A variable part of a URL, like `/vocabulary/{word_id}`.

**Polling**
Repeatedly checking for updates at regular intervals.

**Preflight Request**
An OPTIONS request the browser sends before certain CORS requests.

**Primary Key**
A unique identifier for each row in a database table.

**Props**
Data passed from a parent component to a child component in React.

**Proxy**
An intermediary that forwards requests. Used in development to avoid CORS.

**Pydantic**
Python library for data validation using type hints.

## Q

**Query (React Query)**
A request to fetch data that's cached and managed automatically.

**Query Key**
In React Query, an array that uniquely identifies a query for caching.

**Query Parameter**
Data passed in the URL after `?`, like `?page=2&limit=10`.

## R

**Repository Pattern**
A design pattern that separates data access logic from business logic.

**REST (Representational State Transfer)**
An architectural style for APIs using HTTP methods and resource-based URLs.

**Router**
In FastAPI, a grouping of related endpoints. In React Router, handles URL-to-component mapping.

## S

**Schema**
A definition of data structure. Pydantic schemas define request/response formats.

**Singleton**
A design pattern where only one instance of something exists (like `settings`).

**SPA (Single Page Application)**
A web app that loads once and updates dynamically without full page reloads.

**SQL (Structured Query Language)**
Language for querying and manipulating databases.

**SQLite**
A file-based, embedded database that requires no server.

**State**
Data that changes over time and affects what's rendered. Managed with `useState` in React.

**Status Code**
HTTP response number indicating success (200s), client error (400s), or server error (500s).

## T

**Task**
In our app, a background operation with an ID that can be polled for status.

**ThreadPoolExecutor**
Python class that manages a pool of threads for running tasks concurrently.

**Type Hint**
Python syntax for indicating expected types, like `def greet(name: str) -> str`.

**TypeScript**
JavaScript with static types, catching errors at compile time.

## U

**UUID (Universally Unique Identifier)**
A 128-bit identifier that's practically guaranteed to be unique.

## V

**Validation**
Checking that data meets requirements (correct type, within range, etc.).

**Virtual DOM**
React's in-memory representation of the UI, used to efficiently update the real DOM.

## W

**Webhook**
An HTTP callback - a URL that gets called when an event occurs.

---

[← Previous: Testing with pytest](21-testing-with-pytest.md) | [Back to Index](README.md) | [Next: Common Patterns →](appendix-b-common-patterns.md)
