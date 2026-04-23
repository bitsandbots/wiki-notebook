# API Reference — Wiki Notebook

## Base URL

```
http://localhost:5000/api
```

## Authentication

None required. This is a local, single-user application.

---

## Health

### `GET /api/health`

Check server and dependency status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "database": {
    "connected": true,
    "tables": ["notes", "notes_fts", "note_revisions"]
  },
  "ollama": {
    "reachable": true,
    "model": "qwen2.5:7b-instruct"
  }
}
```

---

## Notes

### `GET /api/notes`

List notes with pagination and filtering.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `category` | — | Filter by category |
| `limit` | 50 | Max results |
| `offset` | 0 | Results to skip |
| `order` | `"new"` | `"new"` or `"old"` |

**Response:**
```json
{
  "items": [...],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### `POST /api/notes`

Create a note. Triggers background AI categorization.

**Body:**
```json
{
  "title": "Note Title",
  "body": "Content",
  "category": "work",
  "tags": ["tag1"]
}
```

**Response:** `201 Created` — note object.

### `GET /api/notes/<id>`

Get a single note.

### `PUT /api/notes/<id>`

Update a note.

**Body:** Same shape as POST (all fields optional).

**Response:** `200 OK` — updated note object.

### `DELETE /api/notes/<id>`

Delete a note permanently.

**Response:** `204 No Content`

---

## Import

### `POST /api/notes/import`

Parse one or more uploaded `.txt`/`.md` files into proposed chunks. **Does not create notes.** The client reviews and confirms chunks via the import preview UI.

**Request:** `multipart/form-data`

- `files` — one or more `.txt` or `.md` files (max 5 MB each)

**Response:**
```json
{
  "chunks": [
    {
      "index": 0,
      "title": "Section Title",
      "body": "Section content…",
      "source_file": "notes.md"
    }
  ],
  "file_count": 1,
  "chunk_count": 4
}
```

**Errors:**
- `400` — no files, unsupported extension
- `413` — file exceeds 5 MB limit

### `POST /api/notes/suggest-title`

Suggest a short title for a chunk of text using Ollama. Used by the import preview "✦" button. Stateless — does not persist anything.

**Body:**
```json
{ "body": "Text to title…" }
```

**Response:**
```json
{ "title": "Suggested Title" }
```

**Errors:**
- `400` — missing body
- `503` — Ollama not reachable
- `502` — Ollama returned an error

---

## Combine

### `POST /api/notes/combine`

Combine multiple notes into a new note.

**Body:**
```json
{
  "note_ids": [1, 2, 3],
  "mode": "concatenate",
  "title": "Combined Note"
}
```

**Modes:**
- `concatenate` — merge with section headers
- `ai` — AI synthesis (requires Ollama)

**Response:** `201 Created` — new combined note.

---

## Search

### `GET /api/search`

Full-text search using FTS5 with BM25 ranking.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `q` | (required) | Search query |
| `category` | — | Filter by category |
| `limit` | 50 | Max results |
| `offset` | 0 | Skip |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Note Title",
      "snippet": "…highlighted <mark>term</mark>…",
      "score": 0.85
    }
  ],
  "total": 3,
  "q": "search term"
}
```

### `GET /api/categories`

List categories with note counts.

**Response:**
```json
{
  "items": [
    {"name": "work", "count": 5},
    {"name": "personal", "count": 3}
  ]
}
```

---

## AI Operations

### `POST /api/notes/<id>/optimize`

Rewrite a note's content with AI. Saves a revision for undo.

**Body:**
```json
{
  "title": "Improved Title",
  "body": "Optimized content"
}
```

**Response:** `200 OK` — updated note.

### `POST /api/notes/<id>/undo`

Restore the note to its state before the last optimize.

**Response:** `200 OK` — restored note.

### `POST /api/notes/<id>/categorize`

Manually re-run categorization on a note.

**Response:** `200 OK` — note with updated `category` and `tags`.

---

## Data Models

### Note

```typescript
interface Note {
  id: number;
  title: string;         // 1–200 characters
  body: string;
  category: string;      // 0–50 characters
  tags: string[];        // each 1–30 chars, max 20
  created_at: string;    // ISO 8601
  updated_at: string;    // ISO 8601
  optimized_at?: string; // set after optimize
  enrichment_pending: boolean;
  source_ids?: number[]; // for combined notes
}
```

## Error Responses

```json
{
  "error": {
    "code": "validation_failed",
    "message": "title must be between 1 and 200 characters"
  }
}
```

Common codes: `validation_failed` (422), `not_found` (404), `missing_body` (400), `ollama_unavailable` (503), `internal_server_error` (500).
