# Learning Guide: Full-Stack Development with FastAPI & React

A wiki-style learning guide using the El Pais Vocabulary Builder as a teaching example.

## About This Guide

This guide teaches modern full-stack development concepts through a real working application. Each topic uses actual code from the project to explain concepts, with intuitions and practical examples.

**Target audience**: Developers who know basic Python, have some FastAPI experience, and want to understand React/TypeScript patterns.

**Level**: Intermediate - assumes basic programming knowledge, focuses on framework-specific concepts.

---

## Table of Contents

### Part 1: Foundation Concepts

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Project Overview](01-project-overview.md) | What the app does, architecture, how to run it |
| 02 | [How Web Apps Work](02-how-web-apps-work.md) | Client-server model, HTTP, JSON communication |

### Part 2: Backend (FastAPI)

| # | Topic | Description |
|---|-------|-------------|
| 03 | [FastAPI Basics](03-fastapi-basics.md) | Endpoints, parameters, request/response cycle |
| 04 | [Pydantic Data Validation](04-pydantic-data-validation.md) | Models, field types, constraints, nested models |
| 05 | [Routers and Organization](05-routers-and-organization.md) | Modular code structure with APIRouter |
| 06 | [CRUD Operations](06-crud-operations.md) | GET, POST, DELETE endpoints, pagination |
| 07 | [Background Tasks](07-background-tasks.md) | Async operations, task manager pattern |
| 08 | [Configuration and Settings](08-configuration-and-settings.md) | Environment variables, Pydantic Settings |
| 09 | [Middleware and CORS](09-middleware-and-cors.md) | Request pipeline, browser security |

### Part 3: Frontend (React + TypeScript)

| # | Topic | Description |
|---|-------|-------------|
| 10 | [React Basics for Python Devs](10-react-basics-for-python-devs.md) | Components, JSX, props, useState |
| 11 | [TypeScript Essentials](11-typescript-essentials.md) | Types, interfaces, generics |
| 12 | [Fetching Data with React Query](12-fetching-data-with-react-query.md) | useQuery, caching, loading states |
| 13 | [Mutations and Forms](13-mutations-and-forms.md) | useMutation, form handling, validation |
| 14 | [Custom Hooks](14-custom-hooks.md) | Extracting reusable logic, useTask |
| 15 | [Routing with React Router](15-routing-with-react-router.md) | SPAs, navigation, URL parameters |
| 16 | [Styling with CSS](16-styling-with-css.md) | CSS modules, variables, scoped styles |

### Part 4: Connecting Frontend to Backend

| # | Topic | Description |
|---|-------|-------------|
| 17 | [The API Client Pattern](17-the-api-client-pattern.md) | Centralized API calls, error handling |
| 18 | [Async Workflows](18-async-workflows.md) | Full flow from form submit to result |

### Part 5: Database & Services

| # | Topic | Description |
|---|-------|-------------|
| 19 | [SQLite Basics](19-sqlite-basics.md) | Embedded database, tables, queries |
| 20 | [The Repository Pattern](20-the-repository-pattern.md) | Separating data access from logic |

### Part 6: Testing

| # | Topic | Description |
|---|-------|-------------|
| 21 | [Testing with pytest](21-testing-with-pytest.md) | Fixtures, mocking, test organization |

### Appendices

| # | Topic | Description |
|---|-------|-------------|
| A | [Glossary](appendix-a-glossary.md) | Quick definitions of terms |
| B | [Common Patterns](appendix-b-common-patterns.md) | Pattern reference guide |

---

## How to Use This Guide

1. **Sequential reading**: The chapters build on each other, so reading in order is recommended for beginners.

2. **Reference lookup**: Use the table of contents to jump to specific topics you need.

3. **Follow along**: Clone the repository and explore the actual code as you read each chapter.

4. **Try the exercises**: Many chapters include "Try it yourself" sections to reinforce learning.

---

## Running the Project

```bash
# Clone and setup
git clone <repository-url>
cd el-pais-vocab

# Backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

See [Chapter 1: Project Overview](01-project-overview.md) for detailed setup instructions.

---

## Quick Reference

**Backend stack**: Python, FastAPI, Pydantic, SQLite
**Frontend stack**: React, TypeScript, React Query, React Router
**Key patterns**: Task manager for async ops, repository pattern for data access

---

*This guide was created as a learning resource for developers wanting to understand full-stack development patterns through a real working application.*
