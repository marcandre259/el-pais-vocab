# Chapter 20: The Repository Pattern

[← Previous: SQLite Basics](19-sqlite-basics.md) | [Back to Index](README.md) | [Next: Testing with pytest →](21-testing-with-pytest.md)

---

## What is the Repository Pattern?

The repository pattern separates data access logic from business logic:

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  API / Router    │ ───► │   Repository     │ ───► │    Database      │
│  (HTTP logic)    │      │   (data access)  │      │    (storage)     │
└──────────────────┘      └──────────────────┘      └──────────────────┘

"Give me all words"       "SELECT * FROM..."        SQLite file
```

**Benefits:**
- Business logic doesn't know about SQL
- Easy to swap databases (SQLite → PostgreSQL)
- Testable (mock the repository)
- Single place for data access code

---

## Our Repository: db.py

From `core/db.py`, we have functions that act as a repository:

```python
# Data access functions - the "repository"
def get_all_words(db_path, theme=None) -> List[Dict]: ...
def get_known_lemmas(theme, db_path) -> List[str]: ...
def add_words(words, source, ..., db_path) -> tuple[int, int]: ...
def get_stats(db_path, theme=None) -> Dict: ...
```

**Usage in routers:**

```python
from core import db

@router.get("")
def list_vocabulary(...):
    words = db.get_all_words(settings.db_path, theme=theme)
    # Router doesn't know about SQL, just calls db functions
```

---

## Function-Based Repository

Our approach uses functions instead of classes:

```python
# core/db.py

def get_all_words(db_path: str, theme: Optional[str] = None) -> List[Dict]:
    """Return all vocabulary entries, optionally filtered by theme."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if theme:
        cursor.execute("""
            SELECT ... FROM vocabulary WHERE theme = ? ORDER BY added_at DESC
        """, (theme,))
    else:
        cursor.execute("""
            SELECT ... FROM vocabulary ORDER BY added_at DESC
        """)

    words = []
    for row in cursor.fetchall():
        word_dict = dict(row)
        if word_dict["examples"]:
            word_dict["examples"] = json.loads(word_dict["examples"])
        words.append(word_dict)

    conn.close()
    return words
```

**Why functions over classes?**
- Simpler for small projects
- No object instantiation needed
- Easy to test with temporary databases
- Python-ic approach

---

## The Interface

Our db.py exposes these operations:

```python
# Initialization
def init_db(db_path: str) -> None
def init_theme_registry(db_path: str) -> None

# Main vocabulary
def get_all_words(db_path, theme) -> List[Dict]
def get_known_lemmas(theme, db_path) -> List[str]
def add_words(words, source, ..., db_path) -> tuple[int, int]
def get_stats(db_path, theme) -> Dict

# Theme management
def get_all_themes(db_path) -> List[Dict]
def get_theme_by_table_name(table_name, db_path) -> Optional[Dict]
def create_theme_table(table_name, ..., db_path) -> None
def add_words_to_theme(words, table_name, db_path) -> tuple[int, int]
def get_all_words_from_theme(table_name, db_path) -> List[Dict]
def get_known_lemmas_from_theme(table_name, db_path) -> List[str]
```

**Pattern:** Each function takes `db_path` as a parameter, making testing easy.

---

## Separation of Concerns

**Router (HTTP concerns):**
```python
@router.get("")
def list_vocabulary(
    page: int = Query(default=1),
    page_size: int = Query(default=50),
    theme: Optional[str] = None,
):
    # Get data from repository
    words = db.get_all_words(settings.db_path, theme=theme)

    # Handle HTTP concerns (pagination, response format)
    total = len(words)
    paginated = words[start:end]

    return PaginatedResponse(items=paginated, total=total, ...)
```

**Repository (data access):**
```python
def get_all_words(db_path, theme):
    # Handle database concerns (SQL, connections)
    conn = sqlite3.connect(db_path)
    cursor.execute("SELECT ...")
    return [dict(row) for row in cursor.fetchall()]
```

---

## Consistent Return Types

Repository functions return simple Python types:

```python
# Returns list of dicts
def get_all_words(...) -> List[Dict]:
    return [{"id": 1, "word": "casa", ...}, ...]

# Returns list of strings
def get_known_lemmas(...) -> List[str]:
    return ["querer", "casa", "grande"]

# Returns counts
def add_words(...) -> tuple[int, int]:
    return (new_count, updated_count)

# Returns single dict or None
def get_theme_by_table_name(...) -> Optional[Dict]:
    return {"table_name": "vocab_cooking", ...} or None
```

**Why dicts instead of Pydantic models?**
- Repository is core module, shouldn't depend on API schemas
- Simpler, more flexible
- Conversion happens in the API layer

---

## Auto-Initialization Pattern

Our functions auto-initialize the database:

```python
def get_all_words(db_path, theme=None):
    init_db(db_path)  # Ensures table exists
    conn = sqlite3.connect(db_path)
    # ...

def get_stats(db_path, theme=None):
    init_db(db_path)  # Safe to call multiple times
    conn = sqlite3.connect(db_path)
    # ...
```

`init_db` is idempotent - `CREATE TABLE IF NOT EXISTS` does nothing if table exists.

---

## Testing Benefits

The repository pattern makes testing easy:

```python
# Test with temporary database
@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

def test_add_words(temp_db):
    words = [{"word": "casa", "lemma": "casa", ...}]

    new_count, updated_count = db.add_words(
        words,
        source="test",
        theme="test",
        db_path=temp_db,  # Use temp database
    )

    assert new_count == 1
    assert updated_count == 0
```

---

## Alternative: Class-Based Repository

For larger projects, you might use a class:

```python
class VocabularyRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def get_all(self, theme: Optional[str] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        # ...

    def add(self, words: List[Dict], **kwargs) -> tuple[int, int]:
        # ...

    def delete(self, word_id: int) -> bool:
        # ...

# Usage
repo = VocabularyRepository("vocab.db")
words = repo.get_all(theme="el_pais")
```

---

## Why This Matters

**Without repository (mixed concerns):**

```python
@router.get("")
def list_vocabulary():
    conn = sqlite3.connect("vocab.db")  # Database logic in router
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vocabulary")  # SQL in router
    # ...
```

Problems:
- Router knows too much about storage
- Hard to test without database
- SQL scattered throughout codebase
- Changing database affects many files

**With repository (separated concerns):**

```python
@router.get("")
def list_vocabulary():
    words = db.get_all_words(settings.db_path)  # Clean interface
    # ...
```

Benefits:
- Router only knows about db.get_all_words
- Test by mocking db module
- All SQL in one file
- Swap SQLite for PostgreSQL by changing one file

---

## Summary

| Concept | Purpose |
|---------|---------|
| **Repository** | Encapsulates data access |
| **Function-based** | Simple, no classes needed |
| **db_path parameter** | Enables testing with temp files |
| **Return dicts** | Flexible, layer-independent |
| **Auto-init** | Idempotent initialization |

---

## The Data Access Layer

```
┌──────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  Routers, Schemas, HTTP concerns                             │
├──────────────────────────────────────────────────────────────┤
│                      Core Layer                              │
│  db.py (repository), llm.py, scraper.py                      │
├──────────────────────────────────────────────────────────────┤
│                     Storage Layer                            │
│  SQLite file, external APIs                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Try It Yourself

1. Look at `core/db.py` - all database code is here
2. Look at `api/routers/vocabulary.py` - no SQL, just calls db functions
3. Try writing a new db function for a custom query
4. Write a test that uses the `temp_db` fixture

---

## What's Next?

Speaking of testing, [Chapter 21: Testing with pytest](21-testing-with-pytest.md) shows how to write tests for your repository and other code.

---

[← Previous: SQLite Basics](19-sqlite-basics.md) | [Back to Index](README.md) | [Next: Testing with pytest →](21-testing-with-pytest.md)
