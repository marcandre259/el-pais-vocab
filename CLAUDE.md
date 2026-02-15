# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

El Pais Vocabulary Builder - A CLI and API tool to extract Spanish vocabulary from El Pais articles, translate to French, and sync to Anki. Also supports themed vocabulary generation for any language pair.

## Commands

```bash
# Activate virtual environment (REQUIRED before all commands)
source .venv/bin/activate

# Run the CLI
python main.py <command>

# CLI subcommands:
#   add <url>     - Extract vocabulary from El Pais article
#   theme <desc>  - Generate themed vocabulary (any language pair)
#   list          - List vocabulary words
#   sync          - Sync to Anki (requires Anki running with AnkiConnect)
#   stats         - Show database statistics
#   audio         - Generate audio files for all words
#   export        - Export to CSV

# Run the API server
uvicorn api.app:app --reload

# Run tests
pytest tests/

# Run a single test file
pytest tests/test_db.py

# Run a specific test
pytest tests/test_db.py::TestAddWords::test_add_new_word
```

## Architecture

```
main.py          # CLI entry point (argparse subcommands)
core/            # Core business logic modules
  db.py          # SQLite operations (vocabulary + theme tables)
  llm.py         # Claude API integration (Pydantic structured output + tool use)
  scraper.py     # Article fetching with browser cookie extraction
  audio.py       # gTTS text-to-speech generation
  anki_sync.py   # AnkiConnect API integration
  export.py      # CSV export for Anki
api/             # FastAPI REST API
  app.py         # FastAPI application with CORS middleware
  config.py      # Pydantic settings (env vars prefixed ELPAIS_)
  routers/       # API route handlers (vocabulary, articles, themes, audio, sync, tasks)
  schemas/       # Pydantic request/response models
  services/      # Background task management
```

## Data Flow

1. **Article vocabulary**: URL -> scraper.py (with cookies) -> llm.py (extraction) -> db.py (vocabulary table) -> audio.py -> anki_sync.py
2. **Themed vocabulary**: theme prompt -> llm.py (tool use loop to check existing themes) -> db.py (theme-specific table) -> audio.py -> anki_sync.py

## Key Patterns

- **Database schema**: Main vocabulary uses a single `vocabulary` table with `theme` column. Themed vocabulary creates separate `vocab_{name}` tables registered in `theme_registry`.
- **LLM integration**: Uses `client.messages.parse()` with Pydantic `SelectTranslateOutputList` for article extraction; uses streaming tool-use loop for themed vocabulary generation with `lookup_theme_words` and `list_themes` tools.
- **Duplicate handling**: Existing lemmas get updated with new examples (max 5 per word).
- **Language flexibility**: Article extraction defaults to Spanish->French; themed vocabulary supports any language pair via `--source` and `--target` flags.
- **Audio generation**: Uses gTTS with language code mapping (supports 30+ languages). Rate-limited with 0.5s delay between files.
- **Testing**: Tests use pytest fixtures with temporary SQLite databases (`temp_db` fixture in conftest).

## Environment

Requires `ANTHROPIC_API_KEY` in `.env` file. API settings can be configured via `ELPAIS_*` environment variables.
