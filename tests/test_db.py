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

    def test_does_not_duplicate_lemma_in_same_theme(self, temp_db):
        """Test that adding the same lemma in same theme updates examples instead of duplicating."""
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
                "word": "quiere",
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


class TestGetKnownLemmas:
    """Tests for get_known_lemmas function."""

    def test_returns_empty_for_empty_db(self, temp_db):
        """Test returns empty list for empty database."""
        lemmas = db.get_known_lemmas(theme="test", db_path=temp_db)
        assert lemmas == []

    def test_returns_lemmas_for_theme(self, temp_db):
        """Test returns correct lemmas for a theme."""
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

        lemmas = db.get_known_lemmas(theme="el_pais", db_path=temp_db)
        assert set(lemmas) == {"querer", "casa"}


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


class TestThemeRegistry:
    """Tests for theme registry functions."""

    def test_init_theme_registry_creates_table(self, temp_db):
        """Test that theme registry table is created."""
        db.init_theme_registry(temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='theme_registry'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_sanitize_table_name(self):
        """Test table name sanitization."""
        assert db.sanitize_table_name("cooking vocabulary") == "vocab_cooking_vocabulary"
        assert db.sanitize_table_name("Dutch words for active recall") == "vocab_dutch_words_for_active_recall"
        assert db.sanitize_table_name("Test!@#$%") == "vocab_test"

    def test_create_theme_table(self, temp_db):
        """Test creating a theme table."""
        db.create_theme_table(
            table_name="vocab_cooking",
            theme_description="cooking vocabulary",
            source_lang="Dutch",
            target_lang="English",
            deck_name="Cooking",
            db_path=temp_db,
        )

        # Check theme table exists
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vocab_cooking'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

        # Check theme is registered
        themes = db.get_all_themes(temp_db)
        assert len(themes) == 1
        assert themes[0]["table_name"] == "vocab_cooking"

    def test_add_words_to_theme(self, temp_db):
        """Test adding words to a theme table."""
        db.create_theme_table(
            table_name="vocab_cooking",
            theme_description="cooking vocabulary",
            source_lang="Dutch",
            target_lang="English",
            deck_name="Cooking",
            db_path=temp_db,
        )

        words = [
            {
                "word": "koken",
                "lemma": "koken",
                "pos": "verb",
                "translation": "to cook",
                "examples": ["Ik kook graag"],
            }
        ]

        new_count, updated_count = db.add_words_to_theme(words, "vocab_cooking", temp_db)

        assert new_count == 1
        assert updated_count == 0

        theme_words = db.get_all_words_from_theme("vocab_cooking", temp_db)
        assert len(theme_words) == 1
        assert theme_words[0]["lemma"] == "koken"

    def test_get_known_lemmas_from_theme(self, temp_db):
        """Test getting known lemmas from a theme."""
        db.create_theme_table(
            table_name="vocab_cooking",
            theme_description="cooking vocabulary",
            source_lang="Dutch",
            target_lang="English",
            deck_name="Cooking",
            db_path=temp_db,
        )

        words = [
            {"word": "koken", "lemma": "koken", "pos": "verb", "translation": "to cook", "examples": []},
            {"word": "bakken", "lemma": "bakken", "pos": "verb", "translation": "to bake", "examples": []},
        ]

        db.add_words_to_theme(words, "vocab_cooking", temp_db)

        lemmas = db.get_known_lemmas_from_theme("vocab_cooking", temp_db)
        assert set(lemmas) == {"koken", "bakken"}
