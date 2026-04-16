# API Reference - Wiki Notebook

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### Health Check

#### `GET /api/health`

Check server health and status of dependent services.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
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

### Notes CRUD

#### `GET /api/notes`

List notes with pagination and filtering.

**Query Parameters:**
- `category` (optional) - Filter by category
- `limit` (default: 50) - Max results
- `offset` (default: 0) - Results to skip
- `order` (default: "new") - "new" or "old"

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Note Title",
      "body": "Note content",
      "category": "work",
      "tags": ["tag1", "tag2"],
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "enrichment_pending": false
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### `POST /api/notes`

Create a new note.

**Request Body:**
```json
{
  "title": "Note Title",
  "body": "Note content",
  "category": "work",
  "tags": ["tag1", "tag2"]
}
```

**Response:** `201 Created`

#### `GET /api/notes/<id>`

Get a specific note.

**Response:**
```json
{
  "id": 1,
  "title": "Note Title",
  "body": "Note content",
  "category": "work",
  "tags": ["tag1", "tag2"],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "optimized_at": "2024-01-01T00:00:00"
}
```

#### `PUT /api/notes/<id>`

Update a note.

**Request Body:**
```json
{
  "title": "Updated Title",
  "body": "Updated content"
}
```

**Response:** `200 OK`

#### `DELETE /api/notes/<id>`

Delete a note.

**Response:** `204 No Content`

---

### Search

#### `GET /api/search`

Search notes using FTS5 with BM25 ranking.

**Query Parameters:**
- `q` (required) - Search query
- `category` (optional) - Filter by category
- `limit` (default: 50) - Max results
- `offset` (default: 0) - Results to skip

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Note Title",
      "body": "Note content",
      "category": "work",
      "tags": ["tag1"],
      "score": 0.85,
      "snippet": "...<mark>search</mark> result..."
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0,
  "q": "search query"
}
```

#### `GET /api/categories`

List all categories with note counts.

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

### Multi-Select Operations

#### `POST /api/notes/combine`

Combine multiple notes into a new note.

**Request Body:**
```json
{
  "note_ids": [1, 2, 3],
  "mode": "concatenate",
  "title": "Combined Note"
}
```

**Modes:**
- `concatenate` - Simple merge with headers
- `ai` - Placeholder for AI synthesis

**Response:** `201 Created`

---

### Optimization

#### `POST /api/notes/<id>/optimize`

Optimize a note (save revision and update content).

**Request Body:**
```json
{
  "title": "Improved Title",
  "body": "Optimized content"
}
```

**Response:** `200 OK`

#### `POST /api/notes/<id>/undo`

Undo the last optimization by restoring the previous revision.

**Response:** `200 OK`

---

## Data Models

### Note

```typescript
interface Note {
  id: number;
  title: string;        // 1-200 characters
  body: string;         // Required, stripped
  category: string;     // 0-50 characters, optional
  tags: string[];       // 1-30 chars each, max 20
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
  optimized_at?: string; // ISO 8601, when last optimized
  source_ids?: number[]; // For combined notes
}
```

### Search Result

```typescript
interface SearchResult {
  id: number;
  title: string;
  body: string;
  category: string;
  tags: string[];
  score: number;        // BM25 relevance score
  snippet: string;      // Highlighted snippet
}
```

## Error Responses

### Validation Error (422)

```json
{
  "error": {
    "code": "validation_failed",
    "message": "title must be between 1 and 200 characters"
  }
}
```

### Not Found (404)

```json
{
  "error": {
    "code": "not_found",
    "message": "note not found"
  }
}
```

### Internal Server Error (500)

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected error occurred"
  }
}
```

## Authentication

**No authentication required.** This is a local, single-user application.

## Rate Limiting

**No rate limiting.** This is a local application.
