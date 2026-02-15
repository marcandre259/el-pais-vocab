# Appendix B: Common Patterns

[← Previous: Glossary](appendix-a-glossary.md) | [Back to Index](README.md)

---

Quick reference for patterns used throughout the codebase.

## Backend Patterns

### FastAPI Endpoint

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/resource", tags=["resource"])

@router.get("", response_model=PaginatedResponse[Item])
def list_items(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    items = get_items()
    # pagination logic
    return PaginatedResponse(items=items, total=total, ...)

@router.get("/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = find_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("", response_model=Item, status_code=201)
def create_item(request: CreateItemRequest):
    item = save_item(request)
    return item

@router.delete("/{item_id}")
def delete_item(item_id: int):
    if not delete_item_by_id(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Deleted"}
```

### Pydantic Model

```python
from pydantic import BaseModel, Field
from typing import Optional

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    count: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True
```

### Background Task

```python
@router.post("/long-operation", response_model=TaskStatus)
async def start_operation(request: OperationRequest):
    task_id = task_manager.create_task(TaskType.OPERATION)

    asyncio.create_task(
        task_manager.run_task(
            task_id,
            sync_function,
            request.param1,
            request.param2,
        )
    )

    return task_manager.get_task(task_id)
```

### Pydantic Settings

```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    db_path: str = "data.db"
    api_prefix: str = "/api"

    @property
    def db_file(self) -> Path:
        return Path(self.db_path)

    class Config:
        env_prefix = "MYAPP_"

settings = Settings()
```

---

## Database Patterns

### SQLite Connection

```python
import sqlite3

def query_data(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Dict-like rows
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM table WHERE id = ?", (id,))
    row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None
```

### Insert with Parameterization

```python
cursor.execute(
    "INSERT INTO table (col1, col2) VALUES (?, ?)",
    (value1, value2)
)
conn.commit()
```

### JSON Storage

```python
import json

# Store
cursor.execute(
    "INSERT INTO table (data) VALUES (?)",
    (json.dumps(python_list),)
)

# Retrieve
row = cursor.fetchone()
data = json.loads(row["data"]) if row["data"] else []
```

### Upsert Pattern

```python
cursor.execute("SELECT id FROM table WHERE key = ?", (key,))
existing = cursor.fetchone()

if existing:
    cursor.execute("UPDATE table SET value = ? WHERE id = ?", (value, existing[0]))
else:
    cursor.execute("INSERT INTO table (key, value) VALUES (?, ?)", (key, value))
```

---

## Frontend Patterns

### React Component

```tsx
interface Props {
  title: string;
  onClick: () => void;
  disabled?: boolean;
}

export function MyComponent({ title, onClick, disabled = false }: Props) {
  return (
    <button onClick={onClick} disabled={disabled}>
      {title}
    </button>
  );
}
```

### useState

```tsx
const [value, setValue] = useState<string>('');
const [items, setItems] = useState<Item[]>([]);
const [loading, setLoading] = useState(false);
```

### useQuery (React Query)

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => fetchResource(id),
  enabled: !!id,
});
```

### useMutation (React Query)

```tsx
const mutation = useMutation({
  mutationFn: createItem,
  onSuccess: (data) => {
    queryClient.invalidateQueries({ queryKey: ['items'] });
  },
  onError: (error) => {
    setError(error.message);
  },
});

// Usage
mutation.mutate({ name: 'New Item' });
```

### Form Handling

```tsx
const [value, setValue] = useState('');
const [error, setError] = useState<string | null>(null);

const handleSubmit = (e: FormEvent) => {
  e.preventDefault();
  if (!value.trim()) {
    setError('Required');
    return;
  }
  mutation.mutate({ value });
};

return (
  <form onSubmit={handleSubmit}>
    <input value={value} onChange={(e) => setValue(e.target.value)} />
    {error && <span className="error">{error}</span>}
    <button type="submit" disabled={mutation.isPending}>
      Submit
    </button>
  </form>
);
```

### Conditional Rendering

```tsx
// Ternary
{isLoading ? <Spinner /> : <Content />}

// Short-circuit
{error && <ErrorMessage error={error} />}

// Early return
if (!data) return <Loading />;
return <Display data={data} />;
```

### Custom Hook

```tsx
export function useMyHook(param: string) {
  const [state, setState] = useState<T | null>(null);

  useEffect(() => {
    // Effect logic
  }, [param]);

  return { state, setState };
}
```

---

## API Client Patterns

### Generic Request

```typescript
async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}
```

### Typed API Methods

```typescript
export async function getItems(): Promise<Item[]> {
  return request<Item[]>('/items');
}

export async function createItem(data: CreateRequest): Promise<Item> {
  return request<Item>('/items', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

---

## Testing Patterns

### Fixture

```python
@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)
```

### Test Class

```python
class TestFeature:
    def test_basic_case(self, fixture):
        result = function(input)
        assert result == expected

    def test_edge_case(self, fixture):
        result = function(edge_input)
        assert result == edge_expected
```

### Arrange-Act-Assert

```python
def test_something(self, temp_db):
    # Arrange
    data = [{"key": "value"}]

    # Act
    result = process(data)

    # Assert
    assert result == expected
```

---

## CSS Patterns

### CSS Module

```css
.container {
  padding: var(--spacing-md);
}

.title {
  font-size: var(--font-size-lg);
  color: var(--color-text);
}

.button {
  background: var(--color-primary);
}

.button:hover {
  background: var(--color-primary-dark);
}
```

### Using CSS Module

```tsx
import styles from './Component.module.css';

<div className={styles.container}>
  <h1 className={styles.title}>Title</h1>
  <button className={`${styles.button} ${styles.large}`}>
    Click
  </button>
</div>
```

---

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Python module | `snake_case.py` | `task_manager.py` |
| Test file | `test_*.py` | `test_db.py` |
| React component | `PascalCase.tsx` | `ArticleForm.tsx` |
| CSS module | `Component.module.css` | `Button.module.css` |
| Hook | `use*.ts` | `useTask.ts` |
| Types | `types.ts` | `api/types.ts` |

---

## Project Structure

```
project/
├── main.py              # CLI entry
├── core/                # Business logic
│   ├── db.py            # Database operations
│   └── ...
├── api/                 # REST API
│   ├── app.py           # FastAPI app
│   ├── config.py        # Settings
│   ├── routers/         # Endpoints
│   ├── schemas/         # Pydantic models
│   └── services/        # Business services
├── frontend/            # React app
│   └── src/
│       ├── api/         # API client
│       ├── components/  # UI components
│       ├── hooks/       # Custom hooks
│       └── pages/       # Page components
└── tests/               # Test files
```

---

[← Previous: Glossary](appendix-a-glossary.md) | [Back to Index](README.md)
