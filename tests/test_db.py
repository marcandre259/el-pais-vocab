"""Tests for database operations."""
import json
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

from core import db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


class TestInitDb:
    """Tests for init_db function."""

    def test_creates_vocabulary_table(self, temp_db):
        """Test that init_db creates the vocabulary table."""
        db.init_db(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "vocabulary"

    def test_vocabulary_table_has_correct_columns(self, temp_db):
        """Test that vocabulary table has all required columns."""
        db.init_db(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(vocabulary)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected_columns = {
            "id",
            "word",
            "lemma",
            "pos",
            "gender",
            "translation",
            "source_lang",
            "target_lang",
            "examples",
            "source",
            "theme",
            "added_at",
        }
        assert columns == expected_columns

    def test_unique_constraint_is_word_theme(self, temp_db):
        """Test that the UNIQUE constraint is on (word, theme)."""
        db.init_db(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='vocabulary'"
        )
        create_sql = cursor.fetchone()[0]
        conn.close()

        assert "UNIQUE(word, theme)" in create_sql


class TestAddWords:
    """Tests for add_words function."""

    def test_adds_new_word(self, temp_db):
        """Test adding a new word to the database."""
        words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir (to want)",
                "gender": None,
                "examples": ["Quiero aprender espanol"],
            }
        ]

        new_count, updated_count = db.add_words(
            words,
            source="https://example.com/article",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        assert new_count == 1
        assert updated_count == 0

    def test_same_word_lemma_theme_updates_examples(self, temp_db):
        """Test that adding the same word+lemma+theme updates examples instead of duplicating."""
        words1 = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Example 1"],
            }
        ]
        words2 = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Example 2"],
            }
        ]

        db.add_words(
            words1,
            source="url1",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )
        new_count, updated_count = db.add_words(
            words2,
            source="url2",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        assert new_count == 0
        assert updated_count == 1

        # Check that examples were merged
        all_words = db.get_all_words(temp_db)
        assert len(all_words) == 1
        assert "Example 1" in all_words[0]["examples"]
        assert "Example 2" in all_words[0]["examples"]

    def test_different_word_forms_same_lemma_allowed(self, temp_db):
        """Test that different word forms of the same lemma are kept as separate entries."""
        words1 = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Yo quiero comer"],
            }
        ]
        words2 = [
            {
                "word": "quiere",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Ella quiere bailar"],
            }
        ]

        db.add_words(
            words1,
            source="url1",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )
        new_count, updated_count = db.add_words(
            words2,
            source="url2",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        assert new_count == 1
        assert updated_count == 0

        all_words = db.get_all_words(temp_db)
        assert len(all_words) == 2

    def test_same_word_allowed_across_different_themes(self, temp_db):
        """Test that the same word can exist in different themes."""
        words = [
            {
                "word": "koken",
                "lemma": "koken",
                "pos": "verb",
                "translation": "to cook",
                "examples": [],
            }
        ]

        db.add_words(
            words,
            source="url1",
            source_lang="Dutch",
            target_lang="English",
            theme="cooking",
            db_path=temp_db,
        )
        new_count, _ = db.add_words(
            words,
            source="url2",
            source_lang="Dutch",
            target_lang="English",
            theme="restaurant vocabulary",
            db_path=temp_db,
        )

        assert new_count == 1

        all_words = db.get_all_words(temp_db)
        assert len(all_words) == 2

    def test_adds_word_with_gender(self, temp_db):
        """Test adding a word with gender field."""
        words = [
            {
                "word": "casa",
                "lemma": "casa",
                "pos": "noun",
                "translation": "maison",
                "gender": "feminine",
                "examples": ["La casa es grande"],
            }
        ]

        db.add_words(
            words,
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        all_words = db.get_all_words(temp_db)
        assert len(all_words) == 1
        assert all_words[0]["gender"] == "feminine"


class TestGetAllWords:
    """Tests for get_all_words function."""

    def test_returns_empty_list_when_no_words(self, temp_db):
        """Test that empty database returns empty list."""
        words = db.get_all_words(temp_db)
        assert words == []

    def test_returns_all_words(self, temp_db):
        """Test that all words are returned."""
        test_words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": [],
            },
            {
                "word": "casa",
                "lemma": "casa",
                "pos": "noun",
                "translation": "maison",
                "examples": [],
            },
        ]

        db.add_words(
            test_words,
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="test_theme",
            db_path=temp_db,
        )

        words = db.get_all_words(temp_db)
        assert len(words) == 2

    def test_filters_by_theme(self, temp_db):
        """Test filtering words by theme."""
        words1 = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": [],
            }
        ]
        words2 = [
            {
                "word": "koken",
                "lemma": "koken",
                "pos": "verb",
                "translation": "to cook",
                "examples": [],
            }
        ]

        db.add_words(
            words1,
            source="url1",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )
        db.add_words(
            words2,
            source="url2",
            source_lang="Dutch",
            target_lang="English",
            theme="cooking",
            db_path=temp_db,
        )

        el_pais_words = db.get_all_words(temp_db, theme="el_pais")
        cooking_words = db.get_all_words(temp_db, theme="cooking")

        assert len(el_pais_words) == 1
        assert el_pais_words[0]["lemma"] == "querer"

        assert len(cooking_words) == 1
        assert cooking_words[0]["lemma"] == "koken"

    def test_parses_examples_json(self, temp_db):
        """Test that examples JSON is parsed correctly."""
        words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Example 1", "Example 2"],
            }
        ]

        db.add_words(
            words,
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        retrieved = db.get_all_words(temp_db)
        assert isinstance(retrieved[0]["examples"], list)
        assert len(retrieved[0]["examples"]) == 2


class TestGetKnownWords:
    """Tests for get_known_words function."""

    def test_returns_empty_for_empty_db(self, temp_db):
        """Test returns empty list for empty database."""
        words = db.get_known_words(theme="test", db_path=temp_db)
        assert words == []

    def test_returns_words_for_theme(self, temp_db):
        """Test returns correct word forms for a theme."""
        words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": [],
            },
            {
                "word": "casa",
                "lemma": "casa",
                "pos": "noun",
                "translation": "maison",
                "examples": [],
            },
        ]

        db.add_words(
            words,
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        known = db.get_known_words(theme="el_pais", db_path=temp_db)
        assert set(known) == {"quiero", "casa"}


class TestGetStats:
    """Tests for get_stats function."""

    def test_returns_zero_for_empty_db(self, temp_db):
        """Test returns zero counts for empty database."""
        stats = db.get_stats(temp_db)
        assert stats["total_words"] == 0

    def test_counts_words_correctly(self, temp_db):
        """Test that word counts are correct."""
        words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": [],
            },
            {
                "word": "casa",
                "lemma": "casa",
                "pos": "noun",
                "translation": "maison",
                "examples": [],
            },
            {
                "word": "grande",
                "lemma": "grande",
                "pos": "adjective",
                "translation": "grand",
                "examples": [],
            },
        ]

        db.add_words(
            words,
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        stats = db.get_stats(temp_db)
        assert stats["total_words"] == 3
        assert stats["by_pos"]["verb"] == 1
        assert stats["by_pos"]["noun"] == 1
        assert stats["by_pos"]["adjective"] == 1

    def test_returns_theme_breakdown(self, temp_db):
        """Test that theme breakdown is included."""
        words1 = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": [],
            }
        ]
        words2 = [
            {
                "word": "koken",
                "lemma": "koken",
                "pos": "verb",
                "translation": "to cook",
                "examples": [],
            }
        ]

        db.add_words(
            words1,
            source="url1",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )
        db.add_words(
            words2,
            source="url2",
            source_lang="Dutch",
            target_lang="English",
            theme="cooking",
            db_path=temp_db,
        )

        stats = db.get_stats(temp_db)
        assert "by_theme" in stats
        assert stats["by_theme"]["el_pais"] == 1
        assert stats["by_theme"]["cooking"] == 1


class TestThemes:
    """Tests for get_themes and search_words functions."""

    def test_get_themes_excludes_el_pais(self, temp_db):
        """Test that get_themes excludes el_pais theme."""
        db.add_words(
            [{"word": "quiero", "lemma": "querer", "pos": "verb", "translation": "vouloir", "examples": []}],
            source="url",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )
        db.add_words(
            [{"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": []}],
            source="url",
            source_lang="Dutch",
            target_lang="English",
            theme="cooking vocabulary",
            db_path=temp_db,
        )

        themes = db.get_themes(temp_db)
        assert len(themes) == 1
        assert themes[0]["theme"] == "cooking vocabulary"
        assert themes[0]["source_lang"] == "Dutch"
        assert themes[0]["target_lang"] == "English"
        assert themes[0]["word_count"] == 1

    def test_get_themes_empty_db(self, temp_db):
        """Test get_themes on empty database."""
        themes = db.get_themes(temp_db)
        assert themes == []

    def test_search_words_all(self, temp_db):
        """Test searching all words in a theme."""
        words = [
            {"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": []},
            {"word": "bakken", "lemma": "bakken", "pos": "verb", "translation": "to bake", "examples": []},
        ]
        db.add_words(words, source="url", source_lang="Dutch", target_lang="English", theme="cooking", db_path=temp_db)

        results = db.search_words("cooking", db_path=temp_db)
        assert len(results) == 2

    def test_search_words_with_filter(self, temp_db):
        """Test searching words with a filter term."""
        words = [
            {"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": []},
            {"word": "bakken", "lemma": "bakken", "pos": "verb", "translation": "to bake", "examples": []},
        ]
        db.add_words(words, source="url", source_lang="Dutch", target_lang="English", theme="cooking", db_path=temp_db)

        results = db.search_words("cooking", search_term="kok", db_path=temp_db)
        assert len(results) == 1
        assert results[0]["lemma"] == "koken"


class TestMigration:
    """Tests for theme-to-vocabulary migration."""

    def test_migrates_theme_tables_to_vocabulary(self, temp_db):
        """Test that theme tables are migrated into the vocabulary table."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create vocabulary table with new constraint
        cursor.execute("""
            CREATE TABLE vocabulary (
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
                UNIQUE(word, lemma, theme)
            )
        """)

        # Create theme_registry
        cursor.execute("""
            CREATE TABLE theme_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL UNIQUE,
                theme_description TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                deck_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER DEFAULT 0
            )
        """)

        # Register a theme
        cursor.execute("""
            INSERT INTO theme_registry (table_name, theme_description, source_lang, target_lang, deck_name)
            VALUES ('vocab_cooking', 'cooking vocabulary', 'Dutch', 'English', 'Cooking')
        """)

        # Create the theme table
        cursor.execute("""
            CREATE TABLE vocab_cooking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                lemma TEXT NOT NULL,
                pos TEXT,
                translation TEXT NOT NULL,
                examples TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lemma)
            )
        """)

        # Add words to the theme table
        cursor.execute("""
            INSERT INTO vocab_cooking (word, lemma, pos, translation, examples)
            VALUES ('koken', 'koken', 'verb', 'to cook', '["Ik kook graag"]')
        """)
        cursor.execute("""
            INSERT INTO vocab_cooking (word, lemma, pos, translation, examples)
            VALUES ('bakken', 'bakken', 'verb', 'to bake', '["Ik bak een taart"]')
        """)

        conn.commit()
        conn.close()

        # Run migration
        db.migrate_themes_to_vocabulary(temp_db)

        # Verify words were migrated
        all_words = db.get_all_words(temp_db, theme="cooking vocabulary")
        assert len(all_words) == 2
        lemmas = {w["lemma"] for w in all_words}
        assert lemmas == {"koken", "bakken"}

        # Verify source_lang and target_lang were set
        assert all_words[0]["source_lang"] == "Dutch"
        assert all_words[0]["target_lang"] == "English"

        # Verify theme tables were dropped
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "vocab_cooking" not in tables
        assert "theme_registry" not in tables
        assert "vocabulary" in tables

    def test_migration_skips_existing_words(self, temp_db):
        """Test that migration doesn't duplicate words already in vocabulary."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Create vocabulary table
        cursor.execute("""
            CREATE TABLE vocabulary (
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
                UNIQUE(word, lemma, theme)
            )
        """)

        # Pre-populate vocabulary with a word that also exists in theme table
        cursor.execute("""
            INSERT INTO vocabulary (word, lemma, pos, translation, source_lang, target_lang, examples, theme)
            VALUES ('koken', 'koken', 'verb', 'to cook', 'Dutch', 'English', '[]', 'cooking vocabulary')
        """)

        # Create theme_registry and theme table
        cursor.execute("""
            CREATE TABLE theme_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL UNIQUE,
                theme_description TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                deck_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO theme_registry (table_name, theme_description, source_lang, target_lang, deck_name)
            VALUES ('vocab_cooking', 'cooking vocabulary', 'Dutch', 'English', 'Cooking')
        """)
        cursor.execute("""
            CREATE TABLE vocab_cooking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                lemma TEXT NOT NULL,
                pos TEXT,
                translation TEXT NOT NULL,
                examples TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lemma)
            )
        """)
        cursor.execute("""
            INSERT INTO vocab_cooking (word, lemma, pos, translation, examples)
            VALUES ('koken', 'koken', 'verb', 'to cook', '["Ik kook graag"]')
        """)

        conn.commit()
        conn.close()

        db.migrate_themes_to_vocabulary(temp_db)

        # Should still have only 1 word (no duplicate)
        all_words = db.get_all_words(temp_db, theme="cooking vocabulary")
        assert len(all_words) == 1

    def test_migration_noop_without_theme_registry(self, temp_db):
        """Test that migration is a no-op when there's no theme_registry table."""
        db.init_db(temp_db)
        # Should not raise
        db.migrate_themes_to_vocabulary(temp_db)

    def test_constraint_migration_from_unique_lemma(self, temp_db):
        """Test that init_db migrates from UNIQUE(lemma) to UNIQUE(word, theme)."""
        # Create old-style table with UNIQUE(lemma)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE vocabulary (
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
        """)
        cursor.execute("""
            INSERT INTO vocabulary (word, lemma, pos, translation, source_lang, target_lang, examples, theme)
            VALUES ('quiero', 'querer', 'verb', 'vouloir', 'Spanish', 'French', '[]', 'el_pais')
        """)
        conn.commit()
        conn.close()

        # Run init_db which should migrate the constraint
        db.init_db(temp_db)

        # Verify new constraint
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vocabulary'")
        create_sql = cursor.fetchone()[0]
        conn.close()

        assert "UNIQUE(word, theme)" in create_sql

        # Verify data was preserved
        words = db.get_all_words(temp_db)
        assert len(words) == 1
        assert words[0]["lemma"] == "querer"
