# Chapter 4: Pydantic Data Validation

[← Previous: FastAPI Basics](03-fastapi-basics.md) | [Back to Index](README.md) | [Next: Routers and Organization →](05-routers-and-organization.md)

---

## Why Validation Matters

Consider this JSON from a client:

```json
{
  "word_count": "fifty",
  "page": -1,
  "email": "not-an-email"
}
```

Without validation, your code might:
- Crash when trying to do math with `"fifty"`
- Return weird results for page `-1`
- Store invalid data in the database

**Garbage in, garbage out.** Validation prevents garbage from getting in.

---

## What is Pydantic?

Pydantic is a data validation library that uses Python type hints. Define what your data should look like, and Pydantic ensures it matches:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# Valid - works fine
user = User(name="Alice", age=30)

# Invalid - raises ValidationError
user = User(name="Bob", age="thirty")  # age must be int
```

FastAPI uses Pydantic models for:
- Request body validation
- Response serialization
- Query/path parameter validation

---

## Basic Model Definition

From `api/schemas/vocabulary.py`:

```python
from pydantic import BaseModel
from typing import Optional

class VocabularyWord(BaseModel):
    """Vocabulary word response model."""

    id: int
    word: str
    lemma: str
    pos: Optional[str] = None
    gender: Optional[str] = None
    translation: str
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    examples: list[str] = []
    source: Optional[str] = None
    theme: str
    added_at: Optional[str] = None
```

**Field types explained:**

| Field | Type | Meaning |
|-------|------|---------|
| `id: int` | Required integer | Must be provided, must be a number |
| `word: str` | Required string | Must be provided, must be text |
| `pos: Optional[str] = None` | Optional string | Can be omitted, defaults to None |
| `examples: list[str] = []` | List of strings | Can be omitted, defaults to empty list |

---

## Optional vs Required Fields

```python
class Example(BaseModel):
    required_field: str           # MUST be provided
    optional_with_none: Optional[str] = None  # Can be omitted
    optional_with_default: str = "default"    # Can be omitted, has default
```

**Valid inputs:**

```python
Example(required_field="hello")  # OK
Example(required_field="hello", optional_with_none="world")  # OK
Example(required_field="hello", optional_with_default="custom")  # OK
```

**Invalid inputs:**

```python
Example()  # Error! required_field is missing
Example(required_field=123)  # Error! must be string
```

---

## Field Constraints

Pydantic's `Field()` lets you add validation rules:

From `api/schemas/articles.py`:

```python
from pydantic import BaseModel, Field, HttpUrl

class ArticleExtractRequest(BaseModel):
    """Request model for article vocabulary extraction."""

    url: HttpUrl = Field(..., description="URL of the El País article")
    browser: str = Field(
        default="chrome",
        description="Browser to use for cookie extraction"
    )
    source_lang: str = Field(default="Spanish")
    target_lang: str = Field(default="French")
    word_count: int = Field(
        default=10,
        ge=1,      # greater than or equal to 1
        le=50,     # less than or equal to 50
        description="Number of words to extract"
    )
    prompt: str = Field(
        default="Select vocabulary useful for a learner",
        description="Custom prompt for word selection"
    )
```

**Common constraints:**

| Constraint | Meaning | Example |
|------------|---------|---------|
| `ge=1` | >= 1 (greater or equal) | `count: int = Field(ge=1)` |
| `le=100` | <= 100 (less or equal) | `count: int = Field(le=100)` |
| `gt=0` | > 0 (greater than) | `price: float = Field(gt=0)` |
| `lt=10` | < 10 (less than) | `rating: int = Field(lt=10)` |
| `min_length=1` | At least 1 character | `name: str = Field(min_length=1)` |
| `max_length=100` | At most 100 characters | `bio: str = Field(max_length=100)` |
| `regex=r"^\d+$"` | Must match pattern | `code: str = Field(regex=r"^\d{4}$")` |

**Special types:**

| Type | Validates |
|------|-----------|
| `HttpUrl` | Valid HTTP/HTTPS URL |
| `EmailStr` | Valid email address |
| `constr(min_length=1)` | Constrained string |
| `conint(ge=0)` | Constrained integer |

---

## Field() vs default value

```python
# These are equivalent for simple defaults:
name: str = "default"
name: str = Field(default="default")

# Use Field() when you need constraints or descriptions:
count: int = Field(default=10, ge=1, le=100, description="How many items")

# Use ... for required fields with descriptions:
url: HttpUrl = Field(..., description="The URL to process")
```

The `...` (Ellipsis) means "required, no default value".

---

## Nested Models

Models can contain other models:

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    address: Address  # Nested model

# Usage:
person = Person(
    name="Alice",
    address={
        "street": "123 Main St",
        "city": "Paris",
        "country": "France"
    }
)
```

From our codebase - `SearchResult` contains a `VocabularyWord`:

```python
class SearchResult(BaseModel):
    """Semantic search result model."""

    word: VocabularyWord  # Nested model
    relevance_explanation: Optional[str] = None
```

---

## Generic Models

Sometimes you want a reusable wrapper. From `api/schemas/vocabulary.py`:

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**How it works:**
- `T` is a placeholder for "any type"
- `Generic[T]` makes the class generic
- `items: list[T]` is a list of whatever `T` is

**Usage:**

```python
# In a route:
@router.get("", response_model=PaginatedResponse[VocabularyWord])
def list_vocabulary(...):
    ...

# Now items will be list[VocabularyWord]
# Response looks like:
{
    "items": [
        {"id": 1, "word": "casa", ...},
        {"id": 2, "word": "perro", ...}
    ],
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10
}
```

This pattern avoids duplicating pagination logic for every resource type.

---

## Model Config

Pydantic models can have configuration:

```python
class VocabularyWord(BaseModel):
    id: int
    word: str
    # ...

    class Config:
        from_attributes = True  # Can create from ORM objects
```

**Common config options:**

| Option | Purpose |
|--------|---------|
| `from_attributes = True` | Allow creating from objects with attributes |
| `extra = "forbid"` | Error if extra fields are passed |
| `extra = "ignore"` | Silently ignore extra fields |
| `str_strip_whitespace = True` | Strip whitespace from strings |

---

## Validation in Action

Let's trace what happens with invalid input:

```python
# Request:
POST /api/articles/extract
{
    "url": "not-a-url",
    "word_count": 1000
}

# Pydantic validation finds two problems:
# 1. "not-a-url" is not a valid HttpUrl
# 2. 1000 > 50 (le=50 constraint)

# FastAPI response (422 Unprocessable Entity):
{
    "detail": [
        {
            "loc": ["body", "url"],
            "msg": "invalid or missing URL scheme",
            "type": "value_error.url.scheme"
        },
        {
            "loc": ["body", "word_count"],
            "msg": "ensure this value is less than or equal to 50",
            "type": "value_error.number.not_le"
        }
    ]
}
```

**Key insight:** You get all validation errors at once, with exact locations and helpful messages. No need to write any validation code yourself.

---

## Creating Models from Data

Several ways to create Pydantic models:

```python
# From keyword arguments
word = VocabularyWord(
    id=1,
    word="casa",
    lemma="casa",
    translation="maison",
    theme="el_pais"
)

# From a dictionary (using **)
data = {"id": 1, "word": "casa", ...}
word = VocabularyWord(**data)

# From an ORM object (with from_attributes=True)
db_row = cursor.fetchone()
word = VocabularyWord.model_validate(db_row)
```

From `api/routers/vocabulary.py`:

```python
# Converting database rows to response models
items = [
    VocabularyWord(
        id=w["id"],
        word=w["word"],
        lemma=w["lemma"],
        pos=w.get("pos"),  # .get() for optional fields
        # ...
    )
    for w in paginated_words
]
```

---

## Serialization (Model → JSON)

Pydantic models serialize to JSON automatically:

```python
word = VocabularyWord(id=1, word="casa", ...)

# To dictionary
word.model_dump()
# {'id': 1, 'word': 'casa', ...}

# To JSON string
word.model_dump_json()
# '{"id": 1, "word": "casa", ...}'
```

FastAPI does this automatically when returning responses.

---

## Request vs Response Models

It's common to have different models for input vs output:

```python
# For creating (input) - no id, it's generated
class VocabularyWordCreate(BaseModel):
    word: str
    lemma: str
    translation: str
    theme: str = "el_pais"

# For reading (output) - includes id and timestamps
class VocabularyWord(BaseModel):
    id: int
    word: str
    lemma: str
    translation: str
    theme: str
    added_at: Optional[str] = None
```

This pattern:
- Prevents clients from setting IDs
- Lets you add server-generated fields to responses
- Makes the API contract clear

---

## Summary

| Concept | Example | Purpose |
|---------|---------|---------|
| **BaseModel** | `class User(BaseModel)` | Define a data structure |
| **Type hints** | `name: str` | Declare field types |
| **Optional** | `Optional[str] = None` | Field can be None |
| **Field()** | `Field(ge=1, le=100)` | Add constraints |
| **Nested models** | `address: Address` | Composition |
| **Generic** | `PaginatedResponse[T]` | Reusable wrappers |
| **Config** | `class Config` | Model behavior |

---

## Try It Yourself

1. Visit `http://localhost:8000/docs`
2. Look at the "Schemas" section at the bottom
3. Try the `/api/articles/extract` endpoint with invalid data
4. See how validation errors are returned

Or in Python:

```python
from api.schemas.articles import ArticleExtractRequest

# Try creating with invalid data
try:
    req = ArticleExtractRequest(
        url="not-a-url",
        word_count=1000
    )
except Exception as e:
    print(e)  # See validation errors
```

---

## What's Next?

Now that you understand how data is validated, [Chapter 5: Routers and Organization](05-routers-and-organization.md) shows how to structure your API into logical groups of endpoints.

---

[← Previous: FastAPI Basics](03-fastapi-basics.md) | [Back to Index](README.md) | [Next: Routers and Organization →](05-routers-and-organization.md)
