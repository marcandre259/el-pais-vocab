# El País Vocabulary Builder

Extract Spanish vocabulary from El País articles, translate to French, and sync to Anki.

## Setup

### 1. Activate Virtual Environment

**CRITICAL**: You MUST activate the virtual environment before running any commands:

```bash
cd /Users/marc/Documents/el-pais-vocab
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file with your API key:

```bash
ANTHROPIC_API_KEY=your_key_here
```

### 4. Setup Anki (for sync feature)

1. Download and install Anki Desktop: https://apps.ankiweb.net/
2. Open Anki
3. Install AnkiConnect addon:
   - Tools → Add-ons → Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki
4. Keep Anki running when syncing

## Usage

**ALWAYS activate virtual environment first:**

```bash
source .venv/bin/activate
```

Then run commands:

```bash
# Add vocabulary from an article
python main.py add <url> --browser firefox

# Create themed vocabulary (any language pair!)
python main.py theme "cooking vocabulary" --source Dutch --target English --count 20

# List all themes
python main.py theme --list

# Sync to Anki (REQUIRES ANKI RUNNING)
python main.py sync          # sync main vocabulary only
python main.py sync --all    # sync all tables (main + themes)

# List known words
python main.py list

# Show statistics
python main.py stats

# Generate audio for all words
python main.py audio

# Export to CSV (fallback method)
python main.py export
```

## Themed Vocabulary

Create vocabulary lists for any language pair and theme:

```bash
# Dutch words for active recall
python main.py theme "active recall nouns" --source Dutch --target English --count 20

# Spanish cooking vocabulary
python main.py theme "cooking vocabulary" --source Spanish --target French --count 20

# List all themes
python main.py theme --list

# The LLM will detect related themes and offer to merge
python main.py theme "kitchen utensils" --source Dutch --target English
# -> "Found related theme: active recall nouns. Add to existing? [Y/n]"

# Force create new theme even if related one exists
python main.py theme "kitchen items" --source Dutch --target English --force-new
```

Each theme gets its own database table and Anki deck.

## Common Issues

### "ModuleNotFoundError" or "No module named X"

**Solution**: You forgot to activate the virtual environment!

```bash
source .venv/bin/activate
```

### "Cannot connect to AnkiConnect"

**Solutions**:
- Ensure Anki desktop app is running
- Verify AnkiConnect addon is installed (code: 2055492159)
- Restart Anki if you just installed the addon

### "python: command not found"

**Solution**: Use `python3` instead:

```bash
python3 main.py sync
```

## Project Structure

```
el-pais-vocab/
├── .venv/             # Virtual environment (activate this!)
├── main.py            # CLI entry point
├── anki_sync.py       # Anki sync via AnkiConnect
├── scraper.py         # Article fetching
├── llm.py             # Claude API
├── db.py              # SQLite database
├── audio.py           # TTS generation
├── export.py          # CSV export
├── vocab.db           # Vocabulary database
├── audio/             # MP3 files
└── .env               # API keys
```

## Quick Start

```bash
# 1. Activate environment
source .venv/bin/activate

# 2a. Add vocabulary from article (Spanish-French)
python main.py add "https://elpais.com/..." --browser firefox

# 2b. Or create themed vocabulary (any language)
python main.py theme "common verbs" --source Dutch --target English --count 20

# 3. Open Anki desktop app

# 4. Sync to Anki
python main.py sync --all    # sync everything
```

## Documentation

See `instructions.md` for detailed technical documentation.
