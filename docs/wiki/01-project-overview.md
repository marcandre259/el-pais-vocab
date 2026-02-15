# Chapter 1: Project Overview

[← Back to Index](README.md) | [Next: How Web Apps Work →](02-how-web-apps-work.md)

---

## What This App Does

The El Pais Vocabulary Builder helps language learners build vocabulary from real-world content. It:

1. **Extracts vocabulary** from El Pais (Spanish newspaper) articles
2. **Translates** words to your target language (default: French)
3. **Generates audio** pronunciation files
4. **Syncs to Anki** flashcard software for spaced repetition learning

Additionally, it supports **themed vocabulary generation** - give it a topic like "kitchen utensils" and it generates relevant vocabulary for any language pair.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                      ┌─────────────────────┐  │
│   │     CLI     │                      │   React Frontend    │  │
│   │  (main.py)  │                      │  (frontend/src/)    │  │
│   └──────┬──────┘                      └──────────┬──────────┘  │
│          │                                        │             │
│          │ direct calls                           │ HTTP/JSON   │
│          │                                        │             │
├──────────┼────────────────────────────────────────┼─────────────┤
│          │                                        │             │
│          │         ┌─────────────────────┐        │             │
│          │         │    FastAPI Server   │        │             │
│          │         │     (api/app.py)    │◄───────┘             │
│          │         └──────────┬──────────┘                      │
│          │                    │                                 │
│          ▼                    ▼                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Core Modules                         │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│   │  │  db.py   │ │  llm.py  │ │ scraper  │ │  audio   │   │   │
│   │  │ Database │ │ Claude   │ │ Articles │ │  gTTS    │   │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                              ▼                                  │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────┐   │
│   │   SQLite    │     │ Claude API  │     │   AnkiConnect   │   │
│   │  Database   │     │ (External)  │     │   (External)    │   │
│   └─────────────┘     └─────────────┘     └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight**: The same core business logic (`core/` modules) is used by both the CLI and the API. This separation means we can add new interfaces without rewriting logic.

---

## File Structure Walkthrough

```
el-pais-vocab/
├── main.py              # CLI entry point (argparse commands)
│
├── core/                # Business logic (shared by CLI and API)
│   ├── db.py            # Database operations
│   ├── llm.py           # Claude API integration
│   ├── scraper.py       # Article fetching
│   ├── audio.py         # Text-to-speech generation
│   ├── anki_sync.py     # Anki integration
│   └── export.py        # CSV export
│
├── api/                 # FastAPI REST API
│   ├── app.py           # Application setup, middleware
│   ├── config.py        # Configuration management
│   ├── routers/         # Endpoint handlers (one per feature)
│   │   ├── vocabulary.py
│   │   ├── articles.py
│   │   ├── themes.py
│   │   ├── audio.py
│   │   ├── sync.py
│   │   └── tasks.py
│   ├── schemas/         # Request/response models
│   │   ├── vocabulary.py
│   │   ├── articles.py
│   │   ├── themes.py
│   │   └── tasks.py
│   └── services/        # Background task management
│       └── task_manager.py
│
├── frontend/            # React application
│   ├── src/
│   │   ├── App.tsx      # Main app with routing
│   │   ├── api/         # API client and types
│   │   ├── components/  # Reusable UI components
│   │   ├── hooks/       # Custom React hooks
│   │   └── pages/       # Page components
│   ├── package.json     # Dependencies
│   └── vite.config.ts   # Build configuration
│
├── tests/               # Test files
│   ├── conftest.py      # Shared fixtures
│   └── test_db.py       # Database tests
│
├── .env                 # Environment variables (not in git)
└── requirements.txt     # Python dependencies
```

---

## Running the Project Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key (for Claude)
- Anki with AnkiConnect plugin (optional, for sync)

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run the API server
uvicorn api.app:app --reload
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API documentation.

### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### Using the CLI

```bash
source .venv/bin/activate

# Extract vocabulary from an article
python main.py add https://elpais.com/some-article

# Generate themed vocabulary
python main.py theme "kitchen utensils" --source spanish --target french

# List all vocabulary
python main.py list

# Sync to Anki (requires Anki running)
python main.py sync
```

---

## The Two Interfaces

This project provides two ways to interact with the same functionality:

### CLI (Command Line Interface)

Best for:
- Quick one-off operations
- Scripting and automation
- Users who prefer terminal workflows

```bash
python main.py add https://elpais.com/article
```

### Web Interface (API + Frontend)

Best for:
- Visual browsing of vocabulary
- Real-time progress feedback
- Users who prefer graphical interfaces

The frontend communicates with the backend via HTTP requests, which we'll explore in detail in [Chapter 2](02-how-web-apps-work.md).

---

## Data Flow Example

Let's trace what happens when you add an article:

```
1. User submits article URL
         │
         ▼
2. Scraper fetches article content
   (handles authentication cookies)
         │
         ▼
3. LLM extracts vocabulary words
   (Claude identifies and translates)
         │
         ▼
4. Database stores words
   (deduplicates, merges examples)
         │
         ▼
5. Audio generates pronunciation
   (gTTS creates MP3 files)
         │
         ▼
6. Sync pushes to Anki
   (creates flashcards)
```

Each step corresponds to a module in `core/`, and the API/CLI orchestrate these steps.

---

## Why This Architecture?

**Separation of concerns**: Each layer has a clear responsibility:
- `core/` - Business logic (what the app does)
- `api/` - HTTP interface (how to access it remotely)
- `frontend/` - User interface (how users see it)
- `main.py` - CLI interface (alternative access method)

**Testability**: Core logic can be tested without HTTP or UI concerns.

**Flexibility**: Add a mobile app? Just call the same API. Need a different database? Only `db.py` changes.

---

## Key Technologies

| Layer | Technology | Why |
|-------|------------|-----|
| Backend Framework | FastAPI | Modern, fast, automatic docs, type hints |
| Data Validation | Pydantic | Type-safe models, validation, serialization |
| Database | SQLite | Simple, file-based, no server needed |
| Frontend Framework | React | Component-based, large ecosystem |
| Type System | TypeScript | Catch errors early, better tooling |
| Data Fetching | React Query | Caching, loading states, refetching |
| Routing | React Router | SPA navigation |
| Build Tool | Vite | Fast development, HMR |

---

## Try It Yourself

1. Clone the repository and set up both backend and frontend
2. Visit `http://localhost:8000/docs` to explore the API documentation
3. Open the frontend at `http://localhost:5173` and add a vocabulary word
4. Look at the SQLite database file to see how data is stored

---

## What's Next?

Before diving into specific technologies, let's understand [how web applications work](02-how-web-apps-work.md) at a fundamental level - the client-server model that makes this all possible.

---

[← Back to Index](README.md) | [Next: How Web Apps Work →](02-how-web-apps-work.md)
