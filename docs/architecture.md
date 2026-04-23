# Architecture — Wiki Notebook

## High-Level Design

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                              │
│  index.html (SPA)   styles.css (Brand v2.1)   app.js (Vanilla ES21) │
│                                                                      │
│  View state machine: "grid" | "detail" | "import-preview"           │
│  navigateTo(view) is the single transition function                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ fetch() / multipart/form-data
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          Backend Layer                               │
│  app.py (Flask factory)   routes/   repository.py   chunking.py     │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌───────────────────────────┐  ┌───────────────────────────────────────┐
│  SQLite + FTS5             │  │  Ollama (local inference)             │
│  notes, note_revisions    │  │  categorize · optimize · suggest title│
│  FTS5 triggers (auto-sync)│  │  OllamaClient.generate() → prompt     │
└───────────────────────────┘  └───────────────────────────────────────┘
```

## View State Machine

```
         ┌────────────────────────────────┐
         │            "grid"              │◄──── Esc / Back / Close
         │  Default home view             │
         │  Note cards, search, sidebar   │
         └───────────────┬────────────────┘
                         │ click card / editNote()
              ┌──────────┴──────────┐
              ▼                     ▼
    ┌─────────────────┐   ┌──────────────────────┐
    │   "detail"      │   │  "import-preview"    │
    │  Full-page edit │   │  Chunk review + drag │
    │  Autosave 2s    │   │  AI title suggest    │
    └─────────────────┘   └──────────────────────┘
```

`state.gridScrollY` is saved before leaving grid and restored on return.

## Data Flows

### Note Creation

```
User types title/body → POST /api/notes → validate → INSERT notes →
  FTS5 trigger syncs → EnrichmentWorker queue → Ollama categorize (async)
```

### File Import

```
User selects .txt/.md → POST /api/notes/import (multipart) →
  chunking.py: headings → paragraphs → word-boundary fallback →
  JSON chunks returned → import-preview UI →
  User edits titles, reorders (drag), checks boxes →
  POST /api/notes (one per checked chunk) → notes created
```

### Autosave

```
User types → debounce 2s → api.update(currentId, {title, body}) →
  state.hasUnsavedChanges = false → stats bar: "Saved"
  (new notes: no currentId → skip, require manual first save)
```

### AI Suggest Title (import preview)

```
User clicks ✦ → POST /api/notes/suggest-title {body} →
  OllamaClient.generate(prompt) → strip/clean → {title} →
  titleInput.value updated, state.importChunks[i].title synced
```

## Core Modules

| Module | Purpose |
|--------|---------|
| `app.py` | Flask factory, blueprint registration |
| `config.py` | Singleton config from env vars |
| `db.py` | `get_conn()`, schema bootstrap with FTS5 triggers |
| `repository.py` | All SQL — CRUD, combine, optimize, undo |
| `models.py` | `Note` dataclass |
| `validation.py` | `ValidationError` + field validators |
| `search.py` | FTS5 / LIKE fallback, BM25 ranking, snippet extraction |
| `chunking.py` | Hybrid `.txt`/`.md` chunker: headings → paragraphs → word-boundary |
| `ai/ollama_client.py` | `OllamaClient.generate()`, `is_available()` |
| `ai/categorize.py` | Ollama categorize + keyword fallback |
| `ai/worker.py` | `EnrichmentWorker` — async queue for background categorization |

## API Routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/health` | Health + dependency status |
| GET | `/api/notes` | List (pagination, category, order) |
| POST | `/api/notes` | Create note |
| GET | `/api/notes/<id>` | Get note |
| PUT | `/api/notes/<id>` | Update note |
| DELETE | `/api/notes/<id>` | Delete note |
| POST | `/api/notes/import` | Parse files → chunks (no DB write) |
| POST | `/api/notes/suggest-title` | AI title for body text (stateless) |
| POST | `/api/notes/combine` | Merge notes |
| POST | `/api/notes/<id>/optimize` | AI rewrite + save revision |
| POST | `/api/notes/<id>/undo` | Restore previous revision |
| POST | `/api/notes/<id>/categorize` | Re-run categorization |
| GET | `/api/search` | FTS5 search with BM25 |
| GET | `/api/categories` | Category list with counts |

## Database Schema

```sql
notes (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,       -- 1-200 chars
  body TEXT NOT NULL,
  category TEXT,             -- 0-50 chars
  tags TEXT,                 -- JSON array
  created_at TEXT,           -- ISO 8601
  updated_at TEXT,
  optimized_at TEXT,         -- set after /optimize
  enrichment_pending INTEGER,
  source_ids TEXT            -- JSON array (combined notes)
)

note_revisions (
  id INTEGER PRIMARY KEY,
  note_id INTEGER REFERENCES notes(id),
  title TEXT,
  body TEXT,
  reason TEXT,               -- 'optimize' | 'combine' | 'manual'
  created_at TEXT
)

-- FTS5 virtual table (porter stemmer, unicode61)
notes_fts USING fts5(title, body, category, tags,
  content='notes', content_rowid='id')

-- Triggers: notes_ai, notes_au, notes_ad keep notes_fts in sync
```

## Security

- **XSS** — DOMPurify (self-hosted vendor file) sanitizes all rendered markdown
- **SQL injection** — parameterized queries throughout `repository.py`
- **Input validation** — `validation.py` enforces length/type on all API inputs
- **File uploads** — `werkzeug.secure_filename`, 5 MB per-file limit, extension allowlist
- **Error messages** — generic codes exposed, not raw exceptions
