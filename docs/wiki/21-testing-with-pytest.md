# Chapter 21: Testing with pytest

[← Previous: The Repository Pattern](20-the-repository-pattern.md) | [Back to Index](README.md) | [Next: Glossary →](appendix-a-glossary.md)

---

## Why Testing Matters

Tests give you confidence to:
- Refactor without fear
- Add features without breaking existing ones
- Catch bugs before users do
- Document expected behavior

---

## pytest Basics

pytest is Python's most popular testing framework:

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_db.py

# Run specific test
pytest tests/test_db.py::TestAddWords::test_adds_new_word

# Verbose output
pytest -v
```

---

## Test File Structure

From `tests/test_db.py`:

```python
"""Tests for database operations."""
import json
import os
import sqlite3
import tempfile

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
```

---

## Fixtures

Fixtures provide setup/teardown for tests:

```python
@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Setup: Create temp file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    yield path  # This is what the test receives

    # Teardown: Clean up
    if os.path.exists(path):
        os.unlink(path)
```

**Usage in tests:**

```python
def test_something(temp_db):  # pytest injects the fixture
    db.init_db(temp_db)
    # temp_db is the path to a fresh database file
```

**Fixture scopes:**
- `function` (default): Run for each test
- `class`: Run once per test class
- `module`: Run once per module
- `session`: Run once for entire test session

---

## Test Classes

Group related tests:

```python
class TestAddWords:
    """Tests for add_words function."""

    def test_adds_new_word(self, temp_db):
        """Test adding a new word to the database."""
        words = [
            {
                "word": "quiero",
                "lemma": "querer",
                "pos": "verb",
                "translation": "vouloir",
                "examples": ["Quiero aprender"],
            }
        ]

        new_count, updated_count = db.add_words(
            words,
            source="https://example.com",
            source_lang="Spanish",
            target_lang="French",
            theme="el_pais",
            db_path=temp_db,
        )

        assert new_count == 1
        assert updated_count == 0

    def test_does_not_duplicate_lemma(self, temp_db):
        """Test that duplicates update instead of insert."""
        words1 = [{"word": "quiero", "lemma": "querer", ...}]
        words2 = [{"word": "quiere", "lemma": "querer", ...}]

        db.add_words(words1, ..., db_path=temp_db)
        new_count, updated_count = db.add_words(words2, ..., db_path=temp_db)

        assert new_count == 0
        assert updated_count == 1
```

---

## Assertions

pytest uses plain `assert` statements:

```python
# Basic assertions
assert result == expected
assert result is not None
assert result is True
assert len(items) == 5

# Collections
assert "querer" in lemmas
assert set(lemmas) == {"querer", "casa"}

# Exceptions
with pytest.raises(ValueError):
    function_that_raises()

# Approximate comparisons
assert result == pytest.approx(3.14159, rel=0.01)
```

---

## Testing Database Code

```python
class TestGetAllWords:
    """Tests for get_all_words function."""

    def test_returns_empty_list_when_no_words(self, temp_db):
        """Test that empty database returns empty list."""
        words = db.get_all_words(temp_db)
        assert words == []

    def test_returns_all_words(self, temp_db):
        """Test that all words are returned."""
        test_words = [
            {"word": "quiero", "lemma": "querer", "pos": "verb", ...},
            {"word": "casa", "lemma": "casa", "pos": "noun", ...},
        ]

        db.add_words(test_words, ..., db_path=temp_db)

        words = db.get_all_words(temp_db)
        assert len(words) == 2

    def test_filters_by_theme(self, temp_db):
        """Test filtering words by theme."""
        # Add words with different themes
        db.add_words([...], theme="el_pais", db_path=temp_db)
        db.add_words([...], theme="cooking", db_path=temp_db)

        el_pais_words = db.get_all_words(temp_db, theme="el_pais")
        cooking_words = db.get_all_words(temp_db, theme="cooking")

        assert len(el_pais_words) == 1
        assert len(cooking_words) == 1
```

---

## Testing Table Schema

```python
def test_vocabulary_table_has_correct_columns(self, temp_db):
    """Test that vocabulary table has all required columns."""
    db.init_db(temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(vocabulary)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()

    expected_columns = {
        "id", "word", "lemma", "pos", "gender",
        "translation", "source_lang", "target_lang",
        "examples", "source", "theme", "added_at",
    }
    assert columns == expected_columns
```

---

## Testing Edge Cases

```python
class TestAddWords:
    def test_handles_string_examples(self, temp_db):
        """Test that string examples are converted to list."""
        words = [
            {
                "word": "casa",
                "lemma": "casa",
                "translation": "maison",
                "examples": "Single example",  # String, not list
            }
        ]

        db.add_words(words, ..., db_path=temp_db)

        retrieved = db.get_all_words(temp_db)
        assert isinstance(retrieved[0]["examples"], list)

    def test_merges_examples_on_duplicate(self, temp_db):
        """Test that examples are merged for duplicates."""
        words1 = [{"lemma": "querer", "examples": ["Example 1"]}]
        words2 = [{"lemma": "querer", "examples": ["Example 2"]}]

        db.add_words(words1, ..., db_path=temp_db)
        db.add_words(words2, ..., db_path=temp_db)

        all_words = db.get_all_words(temp_db)
        assert len(all_words) == 1
        assert "Example 1" in all_words[0]["examples"]
        assert "Example 2" in all_words[0]["examples"]
```

---

## Mocking External Services

For code that calls external APIs:

```python
from unittest.mock import patch, MagicMock

def test_extract_vocabulary():
    # Mock the LLM call
    with patch('core.llm.select_and_translate') as mock_llm:
        mock_llm.return_value = [
            {"word": "casa", "lemma": "casa", "translation": "maison"}
        ]

        result = extract_vocabulary("http://example.com")

        mock_llm.assert_called_once()
        assert result["new_words"] == 1
```

---

## Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── test_db.py           # Database tests
├── test_llm.py          # LLM integration tests
├── test_api.py          # API endpoint tests
└── test_scraper.py      # Scraper tests
```

**conftest.py** - Shared fixtures available to all tests:

```python
# tests/conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_db.py

# Run specific class
pytest tests/test_db.py::TestAddWords

# Run specific test
pytest tests/test_db.py::TestAddWords::test_adds_new_word

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Run tests matching a pattern
pytest -k "add_word"
```

---

## Test Naming Conventions

```python
# Test file: test_<module>.py
test_db.py
test_api.py

# Test class: Test<Feature>
class TestAddWords:
class TestGetAllWords:

# Test method: test_<behavior>
def test_adds_new_word(self):
def test_returns_empty_list_when_no_words(self):
def test_filters_by_theme(self):
```

---

## Docstrings as Documentation

```python
def test_does_not_duplicate_lemma_in_same_theme(self, temp_db):
    """Test that adding the same lemma in same theme updates examples instead of duplicating."""
    # Test code...
```

The docstring explains:
- What behavior is being tested
- Expected outcome
- Any important context

---

## Summary

| Concept | Purpose |
|---------|---------|
| `pytest` | Test runner framework |
| `@pytest.fixture` | Setup/teardown code |
| `assert` | Verify expected behavior |
| `temp_db` | Isolated test database |
| `pytest.raises` | Test for exceptions |
| `unittest.mock` | Mock external services |

---

## Test Patterns

```python
# Arrange - Act - Assert
def test_something(self, fixture):
    # Arrange: Set up test data
    words = [{"word": "casa", ...}]

    # Act: Call the function
    result = db.add_words(words, ...)

    # Assert: Verify the result
    assert result == (1, 0)

# Given - When - Then (same pattern, different words)
def test_duplicate_handling(self, temp_db):
    # Given: A word exists
    db.add_words([{"lemma": "querer", ...}], ..., db_path=temp_db)

    # When: Same lemma is added again
    new, updated = db.add_words([{"lemma": "querer", ...}], ..., db_path=temp_db)

    # Then: It should update, not duplicate
    assert new == 0
    assert updated == 1
```

---

## Try It Yourself

1. Run the existing tests: `pytest tests/test_db.py -v`
2. Add a new test for an edge case you think of
3. Make a test fail to see what the output looks like
4. Try testing a function with mocking

---

## What's Next?

That completes the main content! The appendices provide quick references:
- [Appendix A: Glossary](appendix-a-glossary.md) - Quick term definitions
- [Appendix B: Common Patterns](appendix-b-common-patterns.md) - Pattern reference

---

[← Previous: The Repository Pattern](20-the-repository-pattern.md) | [Back to Index](README.md) | [Next: Glossary →](appendix-a-glossary.md)
