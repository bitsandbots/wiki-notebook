# Core Module Reference - Wiki Notebook

## Overview

This document provides detailed documentation for the core modules of Wiki Notebook.

## Configuration (`config.py`)

### Config Dataclass

```python
@dataclass
class Config:
    bind_host: str      # Server bind address
    port: int           # Server port
    db_path: str        # SQLite database path
    ollama_url: str     # Ollama server URL
    ollama_model: str   # Model name for AI features
    ollama_timeout: int # Request timeout in seconds
```

### Accessing Config

```python
from wiki_notebook.config import config

# Use config directly
host = config.bind_host
port = config.port
```

## Database (`db.py`)

### get_conn()

Returns a database connection with row factory set.

```python
from wiki_notebook.db import get_conn

conn = get_conn()
cursor = conn.cursor()
cursor.execute("SELECT * FROM notes")
```

### init_db()

Initializes the database schema.

```python
from wiki_notebook.db import init_db

init_db("data/notebook.db")
```

## Repository (`repository.py`)

### CRUD Operations

| Function | Description |
|----------|-------------|
| `list_notes()` | List notes with pagination |
| `get_note()` | Get a specific note |
| `create_note()` | Create a new note |
| `update_note()` | Update a note |
| `delete_note()` | Delete a note |

### Advanced Operations

| Function | Description |
|----------|-------------|
| `combine_notes()` | Combine multiple notes |
| `optimize_note()` | Optimize a note with revision |
| `undo_optimize()` | Undo last optimization |
| `write_revision()` | Write a revision entry |
| `latest_revision()` | Get latest revision |
| `pop_latest_revision()` | Get and delete latest revision |
| `update_enrichment()` | Update enrichment fields |

### Usage Examples

```python
from wiki_notebook.repository import *
from wiki_notebook.db import get_conn

conn = get_conn()

# List notes
notes, total = list_notes(conn, limit=50, offset=0)

# Get specific note
note = get_note(conn, 1)

# Create note
note = create_note(conn, {
    "title": "My Note",
    "body": "Note content",
    "category": "work",
    "tags": ["tag1", "tag2"]
})

# Optimize note
note = optimize_note(conn, 1, body="Updated content")

conn.close()
```

## Validation (`validation.py`)

### Validation Functions

| Function | Description |
|----------|-------------|
| `validate_create()` | Validate note creation payload |
| `validate_update()` | Validate note update payload |
| `validate_category()` | Validate category field |
| `validate_tags()` | Validate tags field |

### ValidationError

Raised when validation fails.

```python
from wiki_notebook.validation import ValidationError

try:
    validate_create(payload)
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Search (`search.py`)

### Search Functions

| Function | Description |
|----------|-------------|
| `fts_search()` | Search with FTS5 |
| `like_search()` | Fallback LIKE search |
| `sanitize_query()` | Escape FTS5 special characters |
| `is_short_query()` | Check if query needs LIKE fallback |

### Usage

```python
from wiki_notebook.search import fts_search, sanitize_query
from wiki_notebook.db import get_conn

conn = get_conn()
query = sanitize_query("search query")
results, total = fts_search(conn, query, limit=50)
```

## AI Integration (`ai/`)

### OllamaClient (`ai/ollama_client.py`)

| Method | Description |
|--------|-------------|
| `is_available()` | Check if Ollama is reachable |
| `generate()` | Generate text |
| `generate_json()` | Generate JSON with retry |

### Categorization (`ai/categorize.py`)

| Function | Description |
|----------|-------------|
| `categorize_note()` | Get category and tags from Ollama |
| `categorize_with_fallback()` | Fallback to keyword heuristic |

### Worker (`ai/worker.py`)

| Class | Description |
|-------|-------------|
| `EnrichmentWorker` | Background thread for async enrichment |

## Routes (`routes/`)

### Health (`routes/health.py`)

- `GET /api/health` - Health status

### Notes (`routes/notes.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notes` | GET | List notes |
| `/api/notes` | POST | Create note |
| `/api/notes/<id>` | GET | Get note |
| `/api/notes/<id>` | PUT | Update note |
| `/api/notes/<id>` | DELETE | Delete note |
| `/api/notes/<id>/optimize` | POST | Optimize note |
| `/api/notes/<id>/undo` | POST | Undo optimization |
| `/api/notes/combine` | POST | Combine notes |
| `/api/notes/import` | POST | Parse uploaded files into chunks |
| `/api/notes/suggest-title` | POST | AI-suggest title for body text |

### Search (`routes/search.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | GET | Search notes |
| `/api/categories` | GET | List categories |

## Entry Point (`__main__.py`)

### Command Line Interface

```bash
# Start server
python -m wiki_notebook

# Initialize database
python -m wiki_notebook init
```

## Chunking (`chunking.py`)

### Functions

| Function | Description |
|----------|-------------|
| `chunk_file()` | Split `.txt`/`.md` content into sections |
| `chunk_by_headings()` | Split markdown by heading level |
| `chunk_by_paragraphs()` | Split by double-newline breaks |
| `chunk_by_words()` | Word-boundary fallback for dense text |

Chunks shorter than `MIN_CHUNK_SIZE` (10 chars) are merged into the preceding chunk.

## Data Models (`models.py`)

### Note Dataclass

```python
@dataclass
class Note:
    id: int
    title: str
    body: str
    category: str | None
    tags: list[str]
    created_at: str
    updated_at: str
    optimized_at: str | None
    source_ids: list[int] | None
```

### note_to_dict()

Converts a Note object to a dictionary.

```python
from wiki_notebook.models import note_to_dict, Note

note = Note.from_row(...)
note_dict = note_to_dict(note)
```
