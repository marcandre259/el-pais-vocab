import sqlite3
import json
import re
from typing import List, Dict, Optional
from datetime import datetime


def init_db(db_path: str = "vocab.db") -> None:
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT,
            gender TEXT,
            translation TEXT NOT NULL,
            source_lang TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            examples TEXT,
            source TEXT,
            theme TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lemma)
        )
    """
    )
    conn.commit()
    conn.close()


# ============ Theme Registry Functions ============


def init_theme_registry(db_path: str = "vocab.db") -> None:
    """Create theme_registry table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS theme_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL UNIQUE,
            theme_description TEXT NOT NULL,
            source_lang TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            deck_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            word_count INTEGER DEFAULT 0
        )
    """
    )

    conn.commit()
    conn.close()


def sanitize_table_name(theme: str) -> str:
    """
    Convert theme description to SQL-safe table name.

    Examples:
        "cooking vocabulary" -> "vocab_cooking_vocabulary"
        "Dutch words for active recall" -> "vocab_dutch_words_for_active_recall"
    """
    clean = re.sub(r"[^a-z0-9]+", "_", theme.lower())
    clean = clean.strip("_")[:45]  # Leave room for prefix
    return f"vocab_{clean}"


def create_theme_table(
    table_name: str,
    theme_description: str,
    source_lang: str,
    target_lang: str,
    deck_name: str,
    db_path: str = "vocab.db",
) -> None:
    """Create a new themed vocabulary table and register it."""
    init_theme_registry(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the themed vocabulary table
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT,
            translation TEXT NOT NULL,
            examples TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lemma)
        )
    """
    )

    # Register the theme
    cursor.execute(
        """
        INSERT OR IGNORE INTO theme_registry
        (table_name, theme_description, source_lang, target_lang, deck_name)
        VALUES (?, ?, ?, ?, ?)
    """,
        (table_name, theme_description, source_lang, target_lang, deck_name),
    )

    conn.commit()
    conn.close()


def get_all_themes(db_path: str = "vocab.db") -> List[Dict]:
    """Return all registered themes with metadata."""
    init_theme_registry(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, table_name, theme_description, source_lang, target_lang,
               deck_name, created_at, word_count
        FROM theme_registry
        ORDER BY created_at DESC
    """
    )

    themes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return themes


def get_theme_by_table_name(
    table_name: str, db_path: str = "vocab.db"
) -> Optional[Dict]:
    """Get a specific theme's metadata by table name."""
    init_theme_registry(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, table_name, theme_description, source_lang, target_lang,
               deck_name, created_at, word_count
        FROM theme_registry
        WHERE table_name = ?
    """,
        (table_name,),
    )

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_words_to_theme(
    words: List[Dict], table_name: str, db_path: str = "vocab.db"
) -> tuple[int, int]:
    """
    Insert words into a themed table, handling duplicates by appending examples.

    Args:
        words: List of dicts with keys: word, lemma, pos, translation, examples
        table_name: Name of the theme table
        db_path: Path to SQLite database file

    Returns:
        Tuple of (new_words_count, updated_words_count)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_count = 0
    updated_count = 0

    for word_data in words:
        lemma = word_data["lemma"]

        cursor.execute(
            f"SELECT id, examples FROM {table_name} WHERE lemma = ?", (lemma,)
        )
        existing = cursor.fetchone()

        if existing:
            existing_id, existing_examples_json = existing

            existing_examples = (
                json.loads(existing_examples_json) if existing_examples_json else []
            )
            new_examples = word_data.get("examples", [])

            combined_examples = existing_examples + new_examples
            unique_examples = list(dict.fromkeys(combined_examples))[:5]

            cursor.execute(
                f"""
                UPDATE {table_name}
                SET examples = ?
                WHERE id = ?
            """,
                (json.dumps(unique_examples), existing_id),
            )
            updated_count += 1
        else:
            examples_json = json.dumps(word_data.get("examples", []))
            cursor.execute(
                f"""
                INSERT INTO {table_name} (word, lemma, pos, translation, examples)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    word_data["word"],
                    word_data["lemma"],
                    word_data.get("pos", ""),
                    word_data["translation"],
                    examples_json,
                ),
            )
            new_count += 1

    # Update word count in registry
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_count = cursor.fetchone()[0]
    cursor.execute(
        "UPDATE theme_registry SET word_count = ? WHERE table_name = ?",
        (total_count, table_name),
    )

    conn.commit()
    conn.close()

    return (new_count, updated_count)


def get_all_words_from_theme(table_name: str, db_path: str = "vocab.db") -> List[Dict]:
    """Return all vocabulary entries from a specific theme table."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT id, word, lemma, pos, translation, examples, added_at
        FROM {table_name}
        ORDER BY added_at DESC
    """
    )

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict["examples"]:
            word_dict["examples"] = json.loads(word_dict["examples"])
        words.append(word_dict)

    conn.close()
    return words


def get_known_lemmas_from_theme(
    table_name: str, db_path: str = "vocab.db"
) -> List[str]:
    """Return list of all lemmas in a specific theme table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT lemma FROM {table_name}")
    lemmas = [row[0] for row in cursor.fetchall()]

    conn.close()
    return lemmas


def search_theme_words(
    table_name: str, search_term: Optional[str] = None, db_path: str = "vocab.db"
) -> List[Dict]:
    """
    Search for words in a theme table, optionally filtering by search term.

    Args:
        table_name: Name of the theme table
        search_term: Optional term to filter words (searches lemma and translation)
        db_path: Path to SQLite database file

    Returns:
        List of matching word dicts
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search_term:
        cursor.execute(
            f"""
            SELECT id, word, lemma, pos, translation, examples, added_at
            FROM {table_name}
            WHERE lemma LIKE ? OR translation LIKE ?
            ORDER BY lemma
        """,
            (f"%{search_term}%", f"%{search_term}%"),
        )
    else:
        cursor.execute(
            f"""
            SELECT id, word, lemma, pos, translation, examples, added_at
            FROM {table_name}
            ORDER BY lemma
        """
        )

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict["examples"]:
            word_dict["examples"] = json.loads(word_dict["examples"])
        words.append(word_dict)

    conn.close()
    return words


def get_known_lemmas(theme: str, db_path: str = "vocab.db") -> List[str]:
    """Return list of all lemmas currently in the database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT lemma FROM vocabulary WHERE theme = '{theme}'")
    lemmas = [row[0] for row in cursor.fetchall()]

    conn.close()
    return lemmas


def add_words(
    words: List[Dict], source_url: str, db_path: str = "vocab.db"
) -> tuple[int, int]:
    """
    Insert words into database, handling duplicates by appending examples.

    Args:
        words: List of dicts with keys: word, lemma, pos, french, examples
        source_url: URL of the article source
        db_path: Path to SQLite database file

    Returns:
        Tuple of (new_words_count, updated_words_count)
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_count = 0
    updated_count = 0

    for word_data in words:
        word = word_data["word"]

        cursor.execute("SELECT id, examples FROM vocabulary WHERE word = ?", (word,))
        existing = cursor.fetchone()

        if existing:
            continue
        else:
            examples_json = json.dumps(word_data.get("examples", []))
            cursor.execute(
                """
                INSERT INTO vocabulary (word, lemma, pos, french, examples, source_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    word_data["word"],
                    word_data["lemma"],
                    word_data.get("pos", ""),
                    word_data["french"],
                    examples_json,
                    source_url,
                ),
            )
            new_count += 1

    conn.commit()
    conn.close()

    return (new_count, updated_count)


def get_all_words(db_path: str = "vocab.db") -> List[Dict]:
    """Return all vocabulary entries from the database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, word, lemma, pos, french, examples, source_url, added_at
        FROM vocabulary
        ORDER BY added_at DESC
    """
    )

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict["examples"]:
            word_dict["examples"] = json.loads(word_dict["examples"])
        words.append(word_dict)

    conn.close()
    return words


def get_stats(db_path: str = "vocab.db") -> Dict:
    """Return statistics about the vocabulary database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_words = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT pos, COUNT(*) as count
        FROM vocabulary
        WHERE pos IS NOT NULL AND pos != ''
        GROUP BY pos
        ORDER BY count DESC
    """
    )
    pos_counts = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {"total_words": total_words, "by_pos": pos_counts}
