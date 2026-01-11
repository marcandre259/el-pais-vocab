import sqlite3
import json
from typing import List, Dict
from datetime import datetime


def init_db(db_path: str = "vocab.db") -> None:
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT,
            french TEXT NOT NULL,
            examples TEXT,
            source_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lemma)
        )
    """)

    conn.commit()
    conn.close()


def get_known_lemmas(db_path: str = "vocab.db") -> List[str]:
    """Return list of all lemmas currently in the database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT lemma FROM vocabulary")
    lemmas = [row[0] for row in cursor.fetchall()]

    conn.close()
    return lemmas


def add_words(words: List[Dict], source_url: str, db_path: str = "vocab.db") -> tuple[int, int]:
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
        lemma = word_data['lemma']

        cursor.execute("SELECT id, examples FROM vocabulary WHERE lemma = ?", (lemma,))
        existing = cursor.fetchone()

        if existing:
            existing_id, existing_examples_json = existing

            existing_examples = json.loads(existing_examples_json) if existing_examples_json else []
            new_examples = word_data.get('examples', [])

            combined_examples = existing_examples + new_examples
            unique_examples = list(dict.fromkeys(combined_examples))[:5]

            cursor.execute("""
                UPDATE vocabulary
                SET examples = ?, source_url = ?
                WHERE id = ?
            """, (json.dumps(unique_examples), source_url, existing_id))
            updated_count += 1
        else:
            examples_json = json.dumps(word_data.get('examples', []))
            cursor.execute("""
                INSERT INTO vocabulary (word, lemma, pos, french, examples, source_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                word_data['word'],
                word_data['lemma'],
                word_data.get('pos', ''),
                word_data['french'],
                examples_json,
                source_url
            ))
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

    cursor.execute("""
        SELECT id, word, lemma, pos, french, examples, source_url, added_at
        FROM vocabulary
        ORDER BY added_at DESC
    """)

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict['examples']:
            word_dict['examples'] = json.loads(word_dict['examples'])
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

    cursor.execute("""
        SELECT pos, COUNT(*) as count
        FROM vocabulary
        WHERE pos IS NOT NULL AND pos != ''
        GROUP BY pos
        ORDER BY count DESC
    """)
    pos_counts = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        'total_words': total_words,
        'by_pos': pos_counts
    }
