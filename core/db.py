import sqlite3
import json
from typing import List, Dict, Optional


def init_db(db_path: str = "vocab.db") -> None:
    """Create database tables if they don't exist, and run migrations."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if vocabulary table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'"
    )
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        # Fresh DB: create with correct constraint
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
                UNIQUE(word, theme)
            )
        """
        )
        conn.commit()
    else:
        # Check if constraint needs migration to UNIQUE(word, theme)
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='vocabulary'"
        )
        create_sql = cursor.fetchone()[0]
        if "UNIQUE(word, theme)" not in create_sql or "UNIQUE(word, lemma, theme)" in create_sql:
            _migrate_unique_constraint(conn)

    conn.close()

    # Run theme data migration (separate connection)
    migrate_themes_to_vocabulary(db_path)


def _migrate_unique_constraint(conn: sqlite3.Connection) -> None:
    """Migrate vocabulary table to UNIQUE(word, theme)."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE vocabulary_new (
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
            UNIQUE(word, theme)
        )
    """
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO vocabulary_new
            (id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at)
        SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at
        FROM vocabulary
    """
    )
    cursor.execute("DROP TABLE vocabulary")
    cursor.execute("ALTER TABLE vocabulary_new RENAME TO vocabulary")
    conn.commit()


def migrate_themes_to_vocabulary(db_path: str = "vocab.db") -> None:
    """Migrate all theme tables into the single vocabulary table, then drop them."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if theme_registry exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='theme_registry'"
    )
    if not cursor.fetchone():
        conn.close()
        return

    # Get all theme entries
    cursor.execute(
        "SELECT table_name, theme_description, source_lang, target_lang FROM theme_registry"
    )
    themes = cursor.fetchall()

    for theme_row in themes:
        table_name = theme_row["table_name"]
        theme_description = theme_row["theme_description"]
        source_lang = theme_row["source_lang"]
        target_lang = theme_row["target_lang"]

        # Check if the theme table actually exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if not cursor.fetchone():
            continue

        # Read all rows from the theme table
        cursor.execute(
            f"SELECT word, lemma, pos, translation, examples, added_at FROM [{table_name}]"
        )
        rows = cursor.fetchall()

        for row in rows:
            # Check if (word, theme) already exists
            cursor.execute(
                "SELECT id FROM vocabulary WHERE word = ? AND theme = ?",
                (row["word"], theme_description),
            )
            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO vocabulary
                    (word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at)
                VALUES (?, ?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?)
            """,
                (
                    row["word"],
                    row["lemma"],
                    row["pos"],
                    row["translation"],
                    source_lang,
                    target_lang,
                    row["examples"],
                    theme_description,
                    row["added_at"],
                ),
            )

        # Drop the theme table
        cursor.execute(f"DROP TABLE [{table_name}]")

    # Drop theme_registry
    cursor.execute("DROP TABLE theme_registry")

    conn.commit()
    conn.close()


def get_known_words(theme: str, db_path: str = "vocab.db") -> List[str]:
    """Return list of all word forms currently in the database for a given theme."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT word FROM vocabulary WHERE theme = ?", (theme,))
    words = [row[0] for row in cursor.fetchall()]

    conn.close()
    return words


def add_words(
    words: List[Dict],
    source: str,
    source_lang: str,
    target_lang: str,
    theme: str,
    db_path: str = "vocab.db",
) -> tuple[int, int]:
    """
    Insert words into database, handling duplicates by appending examples.

    Args:
        words: List of dicts with keys: word, lemma, pos, translation, gender, examples
        source: URL or source description
        source_lang: Source language (e.g., "Spanish")
        target_lang: Target language (e.g., "French")
        theme: Theme identifier (e.g., "el_pais")
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

        cursor.execute(
            "SELECT id, examples FROM vocabulary WHERE word = ? AND theme = ?",
            (word, theme),
        )
        existing = cursor.fetchone()

        if existing:
            existing_id, existing_examples_json = existing
            existing_examples = (
                json.loads(existing_examples_json) if existing_examples_json else []
            )
            new_examples = word_data.get("examples", [])
            if isinstance(new_examples, str):
                new_examples = [new_examples]

            combined_examples = existing_examples + new_examples
            unique_examples = list(dict.fromkeys(combined_examples))[:5]

            cursor.execute(
                """
                UPDATE vocabulary
                SET examples = ?
                WHERE id = ?
            """,
                (json.dumps(unique_examples), existing_id),
            )
            updated_count += 1
        else:
            examples = word_data.get("examples", [])
            if isinstance(examples, str):
                examples = [examples]
            examples_json = json.dumps(examples)

            cursor.execute(
                """
                INSERT INTO vocabulary (word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    word_data["word"],
                    word_data["lemma"],
                    word_data.get("pos", ""),
                    word_data.get("gender", ""),
                    word_data["translation"],
                    source_lang,
                    target_lang,
                    examples_json,
                    source,
                    theme,
                ),
            )
            new_count += 1

    conn.commit()
    conn.close()

    return (new_count, updated_count)


def get_all_words(
    db_path: str = "vocab.db", theme: Optional[str] = None
) -> List[Dict]:
    """Return all vocabulary entries from the database, optionally filtered by theme."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if theme:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at
            FROM vocabulary
            WHERE theme = ?
            ORDER BY added_at DESC
        """,
            (theme,),
        )
    else:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at
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


def get_stats(db_path: str = "vocab.db", theme: Optional[str] = None) -> Dict:
    """Return statistics about the vocabulary database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if theme:
        cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE theme = ?", (theme,))
    else:
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_words = cursor.fetchone()[0]

    if theme:
        cursor.execute(
            """
            SELECT pos, COUNT(*) as count
            FROM vocabulary
            WHERE pos IS NOT NULL AND pos != '' AND theme = ?
            GROUP BY pos
            ORDER BY count DESC
        """,
            (theme,),
        )
    else:
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

    # Get theme breakdown
    cursor.execute(
        """
        SELECT theme, COUNT(*) as count
        FROM vocabulary
        GROUP BY theme
        ORDER BY count DESC
    """
    )
    theme_counts = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {"total_words": total_words, "by_pos": pos_counts, "by_theme": theme_counts}


def get_themes(db_path: str = "vocab.db") -> List[Dict]:
    """Return all themes (excluding el_pais) with metadata."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT theme, source_lang, target_lang, COUNT(*) as word_count, MIN(added_at) as created_at
        FROM vocabulary
        WHERE theme != 'el_pais'
        GROUP BY theme, source_lang, target_lang
    """
    )

    themes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return themes


def search_words(
    theme: str, search_term: Optional[str] = None, db_path: str = "vocab.db"
) -> List[Dict]:
    """
    Search for words in a theme, optionally filtering by search term.

    Args:
        theme: Theme name to search in
        search_term: Optional term to filter words (searches lemma and translation)
        db_path: Path to SQLite database file

    Returns:
        List of matching word dicts
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search_term:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at
            FROM vocabulary
            WHERE theme = ? AND (lemma LIKE ? OR translation LIKE ?)
            ORDER BY lemma
        """,
            (theme, f"%{search_term}%", f"%{search_term}%"),
        )
    else:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme, added_at
            FROM vocabulary
            WHERE theme = ?
            ORDER BY lemma
        """,
            (theme,),
        )

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict["examples"]:
            word_dict["examples"] = json.loads(word_dict["examples"])
        words.append(word_dict)

    conn.close()
    return words
