import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
import db


ANKICONNECT_URL = "http://localhost:8765"
MODEL_NAME = "Spanish-French Vocabulary"


def _invoke_anki(action: str, **params) -> dict:
    """
    Invoke AnkiConnect API.

    Args:
        action: AnkiConnect action name
        **params: Parameters for the action

    Returns:
        Result dictionary from AnkiConnect

    Raises:
        ConnectionError: If cannot connect to Anki
        Exception: If AnkiConnect returns an error
    """
    request_json = {
        "action": action,
        "version": 6,
        "params": params
    }

    try:
        response = requests.post(ANKICONNECT_URL, json=request_json, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(
            "Cannot connect to AnkiConnect. "
            "Please ensure Anki is running with AnkiConnect addon installed."
        ) from e

    result = response.json()

    if result.get('error'):
        raise Exception(f"AnkiConnect error: {result['error']}")

    return result['result']


def check_connection() -> bool:
    """
    Test if AnkiConnect is accessible.

    Returns:
        True if connected, False otherwise
    """
    try:
        version = _invoke_anki("version")
        return version >= 6
    except (ConnectionError, Exception):
        return False


def ensure_deck_exists(deck_name: str) -> None:
    """
    Create deck if it doesn't exist.

    Args:
        deck_name: Name of the deck to create
    """
    decks = _invoke_anki("deckNames")

    if deck_name not in decks:
        _invoke_anki("createDeck", deck=deck_name)
        print(f"Created deck: {deck_name}")


def ensure_note_type_exists() -> None:
    """
    Create custom note type with required fields if it doesn't exist.
    """
    model_names = _invoke_anki("modelNames")

    if MODEL_NAME in model_names:
        return

    # Define the note type structure
    model = {
        "modelName": MODEL_NAME,
        "inOrderFields": [
            "Lemma",
            "French",
            "PartOfSpeech",
            "WordAsFound",
            "Example1",
            "Example2",
            "Audio",
            "SourceURL"
        ],
        "css": """
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}

.spanish {
    font-size: 32px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
}

.pos {
    font-size: 14px;
    color: #7f8c8d;
    font-style: italic;
    margin-bottom: 15px;
}

.french {
    font-size: 24px;
    color: #2980b9;
    margin-bottom: 15px;
}

.context {
    font-size: 16px;
    color: #34495e;
    margin-top: 15px;
    margin-bottom: 10px;
}

.example {
    font-size: 14px;
    color: #555;
    font-style: italic;
    margin: 8px 20px;
    text-align: left;
}

.source {
    font-size: 11px;
    color: #95a5a6;
    margin-top: 20px;
}
""",
        "cardTemplates": [
            {
                "Name": "Spanish to French",
                "Front": """<div class="spanish">{{Lemma}}</div>
<div class="pos">({{PartOfSpeech}})</div>
{{Audio}}""",
                "Back": """{{FrontSide}}
<hr id="answer">
<div class="french">{{French}}</div>
{{#WordAsFound}}
<div class="context">Form in article: <i>{{WordAsFound}}</i></div>
{{/WordAsFound}}
{{#Example1}}
<div class="example">• {{Example1}}</div>
{{/Example1}}
{{#Example2}}
<div class="example">• {{Example2}}</div>
{{/Example2}}
{{#SourceURL}}
<div class="source">Source: El País</div>
{{/SourceURL}}"""
            }
        ]
    }

    _invoke_anki("createModel", **model)
    print(f"Created note type: {MODEL_NAME}")


def note_exists(lemma: str, deck_name: str) -> bool:
    """
    Check if a note with the given lemma already exists in the deck.

    Args:
        lemma: The Spanish lemma to search for
        deck_name: Name of the deck to search in

    Returns:
        True if note exists, False otherwise
    """
    # Escape special characters for Anki search
    escaped_lemma = lemma.replace('"', '\\"')
    query = f'deck:"{deck_name}" "Lemma:{escaped_lemma}"'

    try:
        note_ids = _invoke_anki("findNotes", query=query)
        return len(note_ids) > 0
    except Exception:
        # If search fails, assume note doesn't exist to avoid skipping
        return False


def upload_audio(lemma: str, audio_dir: str = "audio") -> str:
    """
    Upload audio file to Anki media collection.

    Args:
        lemma: The lemma (used for filename)
        audio_dir: Directory containing audio files

    Returns:
        Anki audio reference string like "[sound:lemma.mp3]", or empty string if no audio
    """
    audio_path = Path(audio_dir) / f"{lemma}.mp3"

    if not audio_path.exists():
        return ""

    try:
        with open(audio_path, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode('utf-8')

        filename = f"{lemma}.mp3"
        _invoke_anki("storeMediaFile", filename=filename, data=audio_data)

        return f"[sound:{filename}]"
    except Exception as e:
        print(f"Warning: Failed to upload audio for '{lemma}': {e}")
        return ""


def create_note(word: dict, deck_name: str, audio_dir: str = "audio") -> bool:
    """
    Create a single note in Anki.

    Args:
        word: Dictionary with word data from database
        deck_name: Name of the deck to add note to
        audio_dir: Directory containing audio files

    Returns:
        True if note created successfully, False otherwise
    """
    lemma = word['lemma']

    # Parse examples from JSON if needed
    examples = word.get('examples', [])
    if isinstance(examples, str):
        try:
            examples = json.loads(examples)
        except json.JSONDecodeError:
            examples = []

    # Prepare fields
    fields = {
        "Lemma": lemma,
        "French": word['french'],
        "PartOfSpeech": word.get('pos', ''),
        "WordAsFound": word['word'],
        "Example1": examples[0] if len(examples) > 0 else "",
        "Example2": examples[1] if len(examples) > 1 else "",
        "Audio": upload_audio(lemma, audio_dir),
        "SourceURL": word.get('source_url', '')
    }

    note = {
        "deckName": deck_name,
        "modelName": MODEL_NAME,
        "fields": fields,
        "options": {
            "allowDuplicate": False
        },
        "tags": ["el-pais"]
    }

    try:
        _invoke_anki("addNote", note=note)
        return True
    except Exception as e:
        print(f"Error creating note for '{lemma}': {e}")
        return False


def sync_to_anki(
    db_path: str = "vocab.db",
    audio_dir: str = "audio",
    deck_name: str = "el-pais"
) -> Dict[str, int]:
    """
    Sync all vocabulary from database to Anki deck.

    Args:
        db_path: Path to SQLite database
        audio_dir: Directory containing audio files
        deck_name: Name of the Anki deck

    Returns:
        Dictionary with sync statistics: {'added': int, 'skipped': int, 'failed': int}

    Raises:
        ConnectionError: If cannot connect to AnkiConnect
    """
    # Check connection first
    if not check_connection():
        raise ConnectionError(
            "Cannot connect to AnkiConnect.\n\n"
            "First-time setup:\n"
            "1. Open Anki desktop app\n"
            "2. Go to Tools → Add-ons → Get Add-ons\n"
            "3. Enter code: 2055492159\n"
            "4. Restart Anki\n"
            "5. Run sync again\n\n"
            "More info: https://ankiweb.net/shared/info/2055492159"
        )

    # Ensure deck and note type exist
    ensure_deck_exists(deck_name)
    ensure_note_type_exists()

    # Get all words from database
    words = db.get_all_words(db_path)

    if not words:
        print("No words to sync")
        return {'added': 0, 'skipped': 0, 'failed': 0}

    # Sync each word
    stats = {'added': 0, 'skipped': 0, 'failed': 0}

    print(f"\nSyncing {len(words)} words to Anki deck '{deck_name}'...")

    for word in words:
        lemma = word['lemma']

        # Check if note already exists
        if note_exists(lemma, deck_name):
            stats['skipped'] += 1
            continue

        # Create new note
        if create_note(word, deck_name, audio_dir):
            stats['added'] += 1
            print(f"  Added: {lemma}")
        else:
            stats['failed'] += 1

    return stats


# ============ Theme Sync Functions ============


def create_theme_note(word: dict, deck_name: str, audio_dir: str = "audio", tags: Optional[List[str]] = None) -> bool:
    """
    Create a note for a themed vocabulary word.

    Args:
        word: Dictionary with word data from theme table (uses 'translation' instead of 'french')
        deck_name: Name of the deck to add note to
        audio_dir: Directory containing audio files
        tags: Optional list of tags for the note

    Returns:
        True if note created successfully, False otherwise
    """
    lemma = word['lemma']

    # Parse examples from JSON if needed
    examples = word.get('examples', [])
    if isinstance(examples, str):
        try:
            examples = json.loads(examples)
        except json.JSONDecodeError:
            examples = []

    # Prepare fields (note: themed tables use 'translation' instead of 'french')
    fields = {
        "Lemma": lemma,
        "French": word.get('translation', word.get('french', '')),  # Support both field names
        "PartOfSpeech": word.get('pos', ''),
        "WordAsFound": word.get('word', lemma),
        "Example1": examples[0] if len(examples) > 0 else "",
        "Example2": examples[1] if len(examples) > 1 else "",
        "Audio": upload_audio(lemma, audio_dir),
        "SourceURL": word.get('source_url', '')
    }

    note = {
        "deckName": deck_name,
        "modelName": MODEL_NAME,
        "fields": fields,
        "options": {
            "allowDuplicate": False
        },
        "tags": tags or ["themed-vocab"]
    }

    try:
        _invoke_anki("addNote", note=note)
        return True
    except Exception as e:
        print(f"Error creating note for '{lemma}': {e}")
        return False


def sync_theme_to_anki(
    table_name: str,
    deck_name: str,
    db_path: str = "vocab.db",
    audio_dir: str = "audio"
) -> Dict[str, int]:
    """
    Sync a specific themed vocabulary table to its Anki deck.

    Args:
        table_name: Name of the theme table in database
        deck_name: Name of the Anki deck
        db_path: Path to SQLite database
        audio_dir: Directory containing audio files

    Returns:
        Dictionary with sync statistics: {'added': int, 'skipped': int, 'failed': int}
    """
    # Ensure deck and note type exist
    ensure_deck_exists(deck_name)
    ensure_note_type_exists()

    # Get all words from theme table
    words = db.get_all_words_from_theme(table_name, db_path)

    if not words:
        return {'added': 0, 'skipped': 0, 'failed': 0}

    # Sync each word
    stats = {'added': 0, 'skipped': 0, 'failed': 0}
    tags = ["themed-vocab", f"theme-{table_name}"]

    for word in words:
        lemma = word['lemma']

        # Check if note already exists
        if note_exists(lemma, deck_name):
            stats['skipped'] += 1
            continue

        # Create new note
        if create_theme_note(word, deck_name, audio_dir, tags):
            stats['added'] += 1
            print(f"  Added: {lemma}")
        else:
            stats['failed'] += 1

    return stats


def sync_all_themes(
    db_path: str = "vocab.db",
    audio_dir: str = "audio",
    include_main: bool = True
) -> Dict[str, Dict[str, int]]:
    """
    Sync all themed vocabulary tables to their respective Anki decks.

    Args:
        db_path: Path to SQLite database
        audio_dir: Directory containing audio files
        include_main: Whether to also sync the main vocabulary table

    Returns:
        Dictionary mapping deck names to their sync statistics
    """
    # Check connection first
    if not check_connection():
        raise ConnectionError(
            "Cannot connect to AnkiConnect.\n\n"
            "First-time setup:\n"
            "1. Open Anki desktop app\n"
            "2. Go to Tools → Add-ons → Get Add-ons\n"
            "3. Enter code: 2055492159\n"
            "4. Restart Anki\n"
            "5. Run sync again\n\n"
            "More info: https://ankiweb.net/shared/info/2055492159"
        )

    results = {}

    # Sync main vocabulary table if requested
    if include_main:
        print("\nSyncing main vocabulary (el-pais)...")
        try:
            words = db.get_all_words(db_path)
            if words:
                results["el-pais"] = sync_to_anki(db_path, audio_dir, "el-pais")
            else:
                results["el-pais"] = {'added': 0, 'skipped': 0, 'failed': 0}
        except Exception as e:
            print(f"Error syncing main vocabulary: {e}")
            results["el-pais"] = {'added': 0, 'skipped': 0, 'failed': 0, 'error': str(e)}

    # Get all themes and sync each
    themes = db.get_all_themes(db_path)

    for theme in themes:
        table_name = theme['table_name']
        deck_name = theme['deck_name']
        source_lang = theme['source_lang']
        target_lang = theme['target_lang']

        print(f"\nSyncing {deck_name} ({source_lang} -> {target_lang})...")

        try:
            stats = sync_theme_to_anki(table_name, deck_name, db_path, audio_dir)
            results[deck_name] = stats
        except Exception as e:
            print(f"Error syncing {deck_name}: {e}")
            results[deck_name] = {'added': 0, 'skipped': 0, 'failed': 0, 'error': str(e)}

    return results
