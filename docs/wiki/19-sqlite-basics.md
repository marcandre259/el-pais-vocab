# Chapter 19: SQLite Basics

[← Previous: Async Workflows](18-async-workflows.md) | [Back to Index](README.md) | [Next: The Repository Pattern →](20-the-repository-pattern.md)

---

## What is SQLite?

SQLite is an embedded database - it's just a file:

```
vocab.db  ← All your data is in this single file
```

**Key characteristics:**
- No server to install or run
- Zero configuration
- Works everywhere (included with Python)
- Perfect for small-to-medium applications

---

## Creating a Database

From `core/db.py`:

```python
import sqlite3

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
```

**Breaking it down:**

1. **Connect to database** (creates file if doesn't exist):
   ```python
   conn = sqlite3.connect(db_path)
   ```

2. **Get a cursor** (used to execute queries):
   ```python
   cursor = conn.cursor()
   ```

3. **Execute SQL**:
   ```python
   cursor.execute("CREATE TABLE ...")
   ```

4. **Commit changes** (save to disk):
   ```python
   conn.commit()
   ```

5. **Close connection**:
   ```python
   conn.close()
   ```

---

## Table Schema

```sql
CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-generated unique ID
    word TEXT NOT NULL,                     -- Required text field
    lemma TEXT NOT NULL,
    pos TEXT,                               -- Optional (can be NULL)
    gender TEXT,
    translation TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    examples TEXT,                          -- Stores JSON string
    source TEXT,
    theme TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Auto-set on insert
    UNIQUE(lemma)                           -- No duplicate lemmas
)
```

**Column types:**
- `INTEGER` - Whole numbers
- `TEXT` - Strings
- `TIMESTAMP` - Date/time

**Constraints:**
- `PRIMARY KEY` - Unique identifier for each row
- `AUTOINCREMENT` - Automatically assign next number
- `NOT NULL` - Must have a value
- `UNIQUE` - No duplicates allowed
- `DEFAULT` - Value if not specified

---

## Inserting Data

```python
def add_words(words, source, source_lang, target_lang, theme, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for word_data in words:
        examples_json = json.dumps(word_data.get("examples", []))

        cursor.execute(
            """
            INSERT INTO vocabulary
            (word, lemma, pos, gender, translation, source_lang, target_lang, examples, source, theme)
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

    conn.commit()
    conn.close()
```

**Key pattern: Parameterized queries**

```python
# SAFE - Parameters are escaped
cursor.execute("INSERT INTO t (name) VALUES (?)", (name,))

# DANGEROUS - SQL injection vulnerability!
cursor.execute(f"INSERT INTO t (name) VALUES ('{name}')")
```

The `?` placeholders prevent SQL injection attacks.

---

## Querying Data

```python
def get_all_words(db_path, theme=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return dicts instead of tuples
    cursor = conn.cursor()

    if theme:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation,
                   source_lang, target_lang, examples, source, theme, added_at
            FROM vocabulary
            WHERE theme = ?
            ORDER BY added_at DESC
            """,
            (theme,),
        )
    else:
        cursor.execute(
            """
            SELECT id, word, lemma, pos, gender, translation,
                   source_lang, target_lang, examples, source, theme, added_at
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
```

**Key patterns:**

1. **Row factory for dict results**:
   ```python
   conn.row_factory = sqlite3.Row
   # Now rows are dict-like instead of tuples
   ```

2. **Conditional WHERE clause**:
   ```python
   if theme:
       cursor.execute("SELECT ... WHERE theme = ?", (theme,))
   else:
       cursor.execute("SELECT ...")
   ```

3. **Fetch results**:
   ```python
   cursor.fetchone()   # Get one row
   cursor.fetchall()   # Get all rows
   cursor.fetchmany(n) # Get n rows
   ```

---

## Updating Data

```python
def update_examples(word_id, new_examples, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE vocabulary
        SET examples = ?
        WHERE id = ?
        """,
        (json.dumps(new_examples), word_id),
    )

    conn.commit()
    conn.close()
```

---

## Deleting Data

```python
def delete_word(word_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))

    conn.commit()
    conn.close()
```

---

## JSON Storage Pattern

SQLite doesn't have a native JSON type, so we store JSON as TEXT:

**Storing:**
```python
examples = ["Example 1", "Example 2"]
examples_json = json.dumps(examples)  # '["Example 1", "Example 2"]'

cursor.execute(
    "INSERT INTO vocabulary (examples, ...) VALUES (?, ...)",
    (examples_json, ...)
)
```

**Retrieving:**
```python
cursor.execute("SELECT examples FROM vocabulary WHERE id = ?", (id,))
row = cursor.fetchone()

if row["examples"]:
    examples = json.loads(row["examples"])  # Back to Python list
else:
    examples = []
```

---

## Handling Duplicates

Our app has a "merge examples on duplicate" pattern:

```python
def add_words(words, ...):
    for word_data in words:
        lemma = word_data["lemma"]

        # Check if exists
        cursor.execute(
            "SELECT id, examples FROM vocabulary WHERE lemma = ? AND theme = ?",
            (lemma, theme),
        )
        existing = cursor.fetchone()

        if existing:
            # Merge examples
            existing_id, existing_examples_json = existing
            existing_examples = json.loads(existing_examples_json) if existing_examples_json else []
            new_examples = word_data.get("examples", [])

            combined = existing_examples + new_examples
            unique_examples = list(dict.fromkeys(combined))[:5]  # Max 5

            cursor.execute(
                "UPDATE vocabulary SET examples = ? WHERE id = ?",
                (json.dumps(unique_examples), existing_id),
            )
            updated_count += 1
        else:
            # Insert new
            cursor.execute("INSERT INTO vocabulary ...", (...))
            new_count += 1
```

---

## Dynamic Table Creation

For themed vocabulary, we create tables dynamically:

```python
def sanitize_table_name(theme: str) -> str:
    """Convert theme to SQL-safe table name."""
    clean = re.sub(r"[^a-z0-9]+", "_", theme.lower())
    clean = clean.strip("_")[:45]
    return f"vocab_{clean}"

# "cooking vocabulary" → "vocab_cooking_vocabulary"
# "Dutch words!" → "vocab_dutch_words"


def create_theme_table(table_name, ...):
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            lemma TEXT NOT NULL,
            ...
        )
        """
    )
```

**Note:** The f-string for table name is safe here because we sanitize it first. Never use f-strings for user-provided values!

---

## Registry Pattern

We track dynamic tables in a registry:

```python
def create_theme_table(table_name, theme_description, ...):
    # Create the table
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ...")

    # Register it
    cursor.execute(
        """
        INSERT OR IGNORE INTO theme_registry
        (table_name, theme_description, source_lang, target_lang, deck_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (table_name, theme_description, source_lang, target_lang, deck_name),
    )
```

This lets us query what themed tables exist:

```python
def get_all_themes(db_path):
    cursor.execute("""
        SELECT table_name, theme_description, word_count, ...
        FROM theme_registry
        ORDER BY created_at DESC
    """)
    return [dict(row) for row in cursor.fetchall()]
```

---

## Aggregation Queries

For statistics:

```python
def get_stats(db_path, theme=None):
    # Count total words
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total = cursor.fetchone()[0]

    # Count by part of speech
    cursor.execute("""
        SELECT pos, COUNT(*) as count
        FROM vocabulary
        WHERE pos IS NOT NULL AND pos != ''
        GROUP BY pos
        ORDER BY count DESC
    """)
    by_pos = {row[0]: row[1] for row in cursor.fetchall()}

    return {"total_words": total, "by_pos": by_pos}
```

---

## Summary

| Operation | SQL | Python |
|-----------|-----|--------|
| Create | `CREATE TABLE` | `cursor.execute(...)` |
| Insert | `INSERT INTO` | `cursor.execute(..., (values,))` |
| Query | `SELECT ... FROM ... WHERE` | `cursor.fetchall()` |
| Update | `UPDATE ... SET ... WHERE` | `cursor.execute(...)` |
| Delete | `DELETE FROM ... WHERE` | `cursor.execute(...)` |
| Commit | - | `conn.commit()` |

---

## Best Practices

1. **Always use parameterized queries** for user input
2. **Close connections** when done (or use context managers)
3. **Use row_factory** for dict-like access
4. **Commit after changes** or they won't persist
5. **Handle JSON serialization** explicitly

---

## Try It Yourself

```bash
# Open the database with sqlite3 CLI
sqlite3 vocab.db

# List tables
.tables

# Show table schema
.schema vocabulary

# Query data
SELECT * FROM vocabulary LIMIT 5;

# Exit
.quit
```

---

## What's Next?

We've seen raw database operations. [Chapter 20: The Repository Pattern](20-the-repository-pattern.md) shows how to organize database code for maintainability.

---

[← Previous: Async Workflows](18-async-workflows.md) | [Back to Index](README.md) | [Next: The Repository Pattern →](20-the-repository-pattern.md)
