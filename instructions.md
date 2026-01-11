# El País Vocabulary Builder

A CLI tool to extract Spanish vocabulary from El País articles, translate to French, and export to Anki.

## Project Status ✅

**Status: Fully Implemented** (as of January 2026)

All core features have been implemented and are functional:

| Module         | Status     | Description                                                                              |
| -------------- | ---------- | ---------------------------------------------------------------------------------------- |
| `main.py`      | ✅ Complete | CLI with argparse: `add`, `list`, `export`, `audio`, `stats`, `sync` commands            |
| `scraper.py`   | ✅ Complete | Fetches El País articles with browser cookie support for paywall bypass                  |
| `llm.py`       | ✅ Complete | Claude Haiku integration (`claude-haiku-4-5-20251001`) with JSON parsing and retry logic |
| `db.py`        | ✅ Complete | SQLite operations: init, add/update words, get lemmas, stats                             |
| `audio.py`     | ✅ Complete | gTTS pronunciation generation with rate limiting                                         |
| `export.py`    | ✅ Complete | Anki-compatible CSV export with audio file references (fallback method)                  |
| `anki_sync.py` | ✅ Complete | Direct Anki sync via AnkiConnect API with automatic note type creation                   |

### Key Implementation Details

- **LLM Model**: Using `claude-haiku-4-5-20251001` for cost-effective vocabulary extraction
- **Browser Support**: Firefox (default), Chrome, Edge, Opera via `browser_cookie3`
- **Audio Format**: MP3 files generated via Google TTS, stored in `audio/` directory
- **Export Format**: Semicolon-separated CSV with `[sound:lemma.mp3]` Anki syntax
- **Duplicate Handling**: Existing lemmas get updated with new examples (max 5 per word)

## Overview

Parse El País articles, use Claude Haiku to intelligently select words based on user prompts and existing vocabulary, store in SQLite, export to Anki-compatible CSV.

## Architecture

```
el-pais-vocab/
├── main.py          # CLI using argparse
├── scraper.py       # fetch article, extract text (with cookie support)
├── llm.py           # Claude API interaction
├── db.py            # SQLite operations
├── audio.py         # pronunciation audio generation
├── export.py        # Anki CSV export
├── audio/           # generated MP3 files
├── vocab.db         # SQLite database (created on first run)
└── .env             # ANTHROPIC_API_KEY
```

## Dependencies

```
anthropic
requests
beautifulsoup4
python-dotenv
browser-cookie3    # extract cookies from Chrome/Firefox
gtts               # Google Text-to-Speech for pronunciation audio
```

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,           -- word as found in article (e.g., "quiere")
    lemma TEXT NOT NULL,          -- base form (e.g., "querer")
    pos TEXT,                     -- part of speech
    french TEXT NOT NULL,         -- French translation
    examples TEXT,                -- JSON array of example sentences
    source_url TEXT,              -- article URL
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lemma)                 -- prevent duplicates by lemma
);
```

When a duplicate word is encountered, UPDATE the existing row to append new examples (keep up to 5 examples max).

## CLI Interface

```bash
# Add vocabulary from an article
python main.py add <url> --prompt "pick 30 words, focus on political terms" --count 30 --browser chrome

# List known words
python main.py list [--limit 50]

# Sync to Anki (via AnkiConnect) - RECOMMENDED
python main.py sync [--deck el-pais] [--db vocab.db] [--audio-dir audio]

# Export to Anki CSV (fallback method)
python main.py export [--output vocab.csv]

# Generate/regenerate audio for all words
python main.py audio

# Show stats
python main.py stats
```

### Flags

- `--browser`: firefox (default) — which browser to extract cookies from
- `--count`: number of words to extract (default: 30)
- `--prompt`: instructions for word selection
- `--output`: export filename (default: vocab.csv)

## Scraper (scraper.py)

1. Fetch the URL with requests, using browser cookies for authentication
2. Parse with BeautifulSoup
3. Extract article text from `<article>` tag or main content div
4. El País uses `article` tag with class patterns — inspect and adapt
5. Return clean text (strip HTML, normalize whitespace)

### Cookie Support

Use `browser_cookie3` to extract cookies from the user's browser:

```python
import browser_cookie3
import requests

def get_article_text(url: str, browser: str = "chrome") -> str:
    """
    Fetch article with browser cookies for paywall bypass.
    browser: "chrome", "firefox", "edge", "opera"
    """
    # Try to load cookies from browser
    try:
        if browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name=".elpais.com")
        elif browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name=".elpais.com")
        elif browser == "edge":
            cookies = browser_cookie3.edge(domain_name=".elpais.com")
        else:
            cookies = browser_cookie3.load(domain_name=".elpais.com")
    except Exception as e:
        print(f"Warning: Could not load {browser} cookies: {e}")
        cookies = None

    response = requests.get(url, cookies=cookies, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    # ... parse with BeautifulSoup
```

### CLI Flag

```bash
python main.py add <url> --browser firefox  # default: chrome
```

If article text is < 500 chars after parsing, warn that authentication may have failed.

## LLM Integration (llm.py)

Use `claude-haiku-4-5-20250929` for cost efficiency.

### Prompt Structure

```python
def select_and_translate(article_text: str, known_words: list[str], user_prompt: str, count: int) -> list[dict]:
    """
    Calls Claude Haiku to select vocabulary words.

    Returns list of dicts with keys: word, lemma, pos, french, examples
    """
```

### System Prompt

```
You are a Spanish-French vocabulary assistant. Given a Spanish news article, select vocabulary words for a French speaker learning Spanish.

Rules:
- Return exactly {count} words as JSON array
- Exclude words already known (provided in list)
- For verbs: "word" = conjugated form found, "lemma" = infinitive
- Include 1-2 example sentences from the article for each word
- "french" should include the translation matching the context, plus infinitive for verbs
- Prioritize useful vocabulary over obscure terms
- Include a mix: verbs, nouns, adjectives, adverbs, prepositions, conjunctions
- Include pronouns and common phrases if relevant to user prompt

Output format (JSON array only, no markdown):
[
  {
    "word": "quiere",
    "lemma": "querer",
    "pos": "verb",
    "french": "veut (vouloir)",
    "examples": ["Trump quiere imponer su ley"]
  }
]
```

### User Message

```
Article text:
{article_text}

Known words (exclude these):
{known_words as comma-separated}

User request: {user_prompt}

Select {count} vocabulary words. Return JSON array only.
```

### Implementation Notes

- Set `max_tokens` appropriately (~2000 for 50 words)
- Parse JSON response, handle potential formatting issues
- If response isn't valid JSON, retry once or raise clear error

## Database Operations (db.py)

```python
def init_db(db_path: str = "vocab.db"):
    """Create tables if not exist"""

def get_known_lemmas(db_path: str = "vocab.db") -> list[str]:
    """Return all lemmas in database"""

def add_words(words: list[dict], source_url: str, db_path: str = "vocab.db"):
    """
    Insert words, handle duplicates by appending examples.
    words: list of dicts from LLM response
    """

def get_all_words(db_path: str = "vocab.db") -> list[dict]:
    """Return all vocabulary entries"""

def get_stats(db_path: str = "vocab.db") -> dict:
    """Return counts by POS, total words, etc."""
```

## Audio Pronunciation (audio.py)

Use `gTTS` (Google Text-to-Speech) to generate MP3 files for each word.

```python
from gtts import gTTS
from pathlib import Path

def generate_audio(lemma: str, audio_dir: str = "audio") -> str:
    """
    Generate MP3 pronunciation for a word.
    Returns path to audio file.
    """
    Path(audio_dir).mkdir(exist_ok=True)
    filepath = f"{audio_dir}/{lemma}.mp3"

    if not Path(filepath).exists():
        tts = gTTS(text=lemma, lang='es', slow=False)
        tts.save(filepath)

    return filepath

def generate_all_audio(lemmas: list[str], audio_dir: str = "audio"):
    """Generate audio for all words, skip existing."""
    for lemma in lemmas:
        generate_audio(lemma, audio_dir)
```

### When to Generate

- Generate audio immediately after adding new words (`main.py add`)
- Or batch generate with `python main.py audio` command

### Rate Limiting

gTTS uses Google Translate's unofficial API. Add small delays between requests to avoid rate limiting:

```python
import time
time.sleep(0.5)  # between each TTS call
```

## Export (export.py)

Anki expects CSV/TSV. Default format:

```
lemma;french;examples;word_as_found;pos;audio
querer;veut (vouloir);Trump quiere imponer su ley;quiere;verb;[sound:querer.mp3]
```

The `[sound:filename.mp3]` syntax is Anki's format for audio references.

```python
def export_csv(output_path: str = "vocab.csv", db_path: str = "vocab.db", audio_dir: str = "audio"):
    """
    Export vocabulary to Anki-compatible CSV.
    - Semicolon separated (configurable)
    - Examples joined with " | "
    - UTF-8 encoding
    - Audio column references MP3 files
    """
```

### Anki Import Instructions

1. Export with `python main.py export --output vocab.csv`
2. Copy entire `audio/` folder to Anki's media folder:
   - Linux: `~/.local/share/Anki2/<profile>/collection.media/`
   - macOS: `~/Library/Application Support/Anki2/<profile>/collection.media/`
   - Windows: `%APPDATA%\Anki2\<profile>\collection.media\`
3. Import CSV in Anki: File → Import, select the CSV, map fields to card template

## Error Handling

- Network errors: retry once, then fail with clear message
- Paywall detection: warn if article text < 500 chars
- API errors: surface Anthropic error messages
- JSON parse errors: show raw response for debugging
- Cookie extraction errors: warn and attempt without cookies, suggest browser alternative

### browser_cookie3 Troubleshooting

- Chrome: may require closing Chrome completely, or may fail if Chrome profile is encrypted
- Firefox: most reliable, works with browser open
- If cookie extraction fails: manually export cookies to `cookies.txt` file (Netscape format) as fallback

## Environment

Requires `ANTHROPIC_API_KEY` in environment or `.env` file.

## Example Session

```bash
$ python main.py add "https://elpais.com/internacional/2026-01-11/trump-quiere-imponer-su-ley.html" --prompt "pick words including common verbs and political vocabulary" --count 40 --browser firefox

Fetching article (using Firefox cookies)...
Found 1,247 words in article
Known vocabulary: 156 lemmas
Asking Claude to select 40 new words...
Added 40 words (38 new, 2 updated with examples)
Generating audio pronunciations...
Generated 38 new audio files

$ python main.py stats
Total vocabulary: 194 words
By type: verb (67), noun (89), adjective (23), other (15)
Audio files: 194

$ python main.py export --output spanish_vocab.csv
Exported 194 words to spanish_vocab.csv
Audio files in: audio/
Copy audio/ contents to Anki media folder before importing CSV
```

## Future Enhancements (not for initial build)

- Spaced repetition metadata (ease, interval)
- Direct Anki integration via AnkiConnect
- Web UI
- Multiple source support (other Spanish news sites)
