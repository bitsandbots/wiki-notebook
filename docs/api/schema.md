# API Schema - Wiki Notebook

## Note Schema

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Auto | Primary key |
| `title` | string | Yes | 1-200 characters |
| `body` | string | Yes | Any length, stripped |
| `category` | string | No | 0-50 characters, lowercase |
| `tags` | array | No | Array of strings (1-30 chars each, max 20) |
| `created_at` | string | Auto | ISO 8601 timestamp |
| `updated_at` | string | Auto | ISO 8601 timestamp |
| `optimized_at` | string | Optional | ISO 8601 timestamp |
| `source_ids` | array | Optional | Array of note IDs for combined notes |

### Example Note

```json
{
  "id": 1,
  "title": "Project Ideas",
  "body": "Here are some project ideas:\n1. AI project\n2. Web app",
  "category": "work",
  "tags": ["ideas", "planning"],
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-02T14:30:00",
  "optimized_at": "2024-01-02T14:30:00",
  "source_ids": []
}
```

## Search Result Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Note ID |
| `title` | string | Note title |
| `body` | string | Note content |
| `category` | string | Note category |
| `tags` | array | Array of tags |
| `score` | float | BM25 relevance score (0-1) |
| `snippet` | string | Highlighted snippet with `<mark>` tags |

### Example Search Result

```json
{
  "id": 1,
  "title": "Project Ideas",
  "body": "Project ideas for Q1",
  "category": "work",
  "tags": ["ideas"],
  "score": 0.85,
  "snippet": "...<mark>project</mark> ideas for Q1..."
}
```

## List Response Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | Array of notes or search results |
| `total` | integer | Total number of results |
| `limit` | integer | Limit applied |
| `offset` | integer | Offset applied |

### Example Response

```json
{
  "items": [...],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

## Error Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Error code (e.g., "validation_failed") |
| `message` | string | Human-readable error message |

### Example Error

```json
{
  "error": {
    "code": "validation_failed",
    "message": "title is required and must be between 1 and 200 characters"
  }
}
```

## Category Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Category name |
| `count` | integer | Number of notes in category |

### Example Category List

```json
{
  "items": [
    {"name": "work", "count": 15},
    {"name": "personal", "count": 8},
    {"name": "ideas", "count": 5}
  ]
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created |
| 204 | No Content - Deletion successful |
| 400 | Bad Request - Malformed request |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation failed |
| 500 | Internal Server Error - Server error |
