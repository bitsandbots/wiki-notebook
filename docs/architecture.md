# Architecture - Wiki Notebook

## High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   index.html │  │  styles.css  │  │   app.js     │              │
│  │   (SPA)      │  │   (CSS)      │  │  (Vanilla)   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   app.py     │  │   routes/    │  │  repository  │              │
│  │   (Flask)    │  │   (API)      │  │   (SQL)      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data & AI Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  SQLite      │  │  FTS5        │  │  Ollama      │              │
│  │  (Database)  │  │  (Search)    │  │  (AI)        │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Note Creation Flow

```
User Input → Validation → Repository → SQLite + FTS5 → Enqueue AI → Response
     │           │            │              │             │          │
     ▼           ▼            ▼              ▼             ▼          ▼
  Title    Category/tags   Insert note   FTS sync    Enrichment  JSON
  Body     Tags                              Worker    (async)
```

### Search Flow

```
User Query → Sanitize → FTS5/LIKE → BM25 Ranking → Snippets → Results
     │           │          │           │              │          │
     ▼           ▼          ▼           ▼              ▼          ▼
  Query   Escaped chars  Search      Relevance    Highlights  JSON
```

### Optimize Flow

```
Optimize Request → Save Revision → Update Note → Return Result
        │                │               │            │
        ▼                ▼               ▼            ▼
    Payload           Revision       New content  JSON
```

## Component Details

### Core Modules

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `config.py` | Environment configuration | `Config` dataclass |
| `db.py` | Database connection | `get_conn()`, `init_db()` |
| `repository.py` | Data access layer | CRUD + combine + optimize |
| `models.py` | Data models | `Note` dataclass |
| `validation.py` | Input validation | `ValidationError`, validators |
| `search.py` | Search orchestration | `fts_search()`, `sanitize_query()` |
| `ai/ollama_client.py` | Ollama HTTP client | `OllamaClient` class |
| `ai/worker.py` | Async enrichment | `EnrichmentWorker` class |
| `ai/categorize.py` | Category assignment | `categorize_note()` |

### Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/health` | GET | Health status |
| `/api/notes` | GET | List notes |
| `/api/notes` | POST | Create note |
| `/api/notes/<id>` | GET | Get note |
| `/api/notes/<id>` | PUT | Update note |
| `/api/notes/<id>` | DELETE | Delete note |
| `/api/notes/combine` | POST | Combine notes |
| `/api/notes/<id>/optimize` | POST | Optimize note |
| `/api/notes/<id>/undo` | POST | Undo optimize |
| `/api/search` | GET | Search notes |
| `/api/categories` | GET | List categories |

## Database Schema

### Main Tables

```sql
notes (
  id            INTEGER PRIMARY KEY,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  category      TEXT,
  tags          TEXT,           -- JSON array
  created_at    TEXT,
  updated_at    TEXT,
  optimized_at  TEXT,
  source_ids    TEXT            -- JSON array for combined notes
)

note_revisions (
  id          INTEGER PRIMARY KEY,
  note_id     INTEGER REFERENCES notes(id),
  title       TEXT,
  body        TEXT,
  reason      TEXT,             -- 'optimize', 'combine', 'manual'
  created_at  TEXT
)
```

### FTS5 Virtual Table

```sql
notes_fts USING fts5(
  title, body, category, tags,
  content='notes', content_rowid='id'
)
```

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | Python | 3.11+ |
| Web Framework | Flask | Latest |
| Database | SQLite | Latest |
| Search | FTS5 | Built-in |
| AI | Ollama | Latest |
| Frontend | Vanilla JS | ES2021+ |
| Styling | CSS | Modern |
| Build | Hatch | Latest |

## Security Considerations

- **XSS Protection**: DOMPurify for client-side sanitization
- **SQL Injection**: Parameterized queries throughout
- **Input Validation**: Pydantic-style validation on all endpoints
- **Error Handling**: Generic error messages to avoid information leakage
