# Tech Stack - Wiki Notebook

## Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| Flask | Latest | Web framework |
| SQLite | Latest | Database |
| Ollama | Latest | AI inference |
| Hatch | Latest | Build system |

## Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| HTML5 | Latest | Markup |
| CSS3 | Latest | Styling |
| Vanilla JS | ES2021+ | Logic |
| DOMPurify | Latest | XSS protection |
| marked.js | Latest | Markdown rendering |

## Database

| Technology | Version | Purpose |
|------------|---------|---------|
| SQLite | Latest | Primary database |
| FTS5 | Built-in | Full-text search |
| FTS5 Porter Stemmer | Built-in | Text stemming |

## Development Tools

| Technology | Version | Purpose |
|------------|---------|---------|
| pytest | Latest | Testing |
| black | Latest | Code formatting |
| isort | Latest | Import sorting |
| typeguard | Latest | Type checking |

## Deployment

| Technology | Version | Purpose |
|------------|---------|---------|
| systemd | Latest | Service management |
| Apache/Nginx | Latest | Web server (optional) |

## System Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | Any modern CPU |
| RAM | 512MB minimum (1GB+ recommended) |
| Storage | 1GB+ for database and assets |
| OS | Linux (Raspberry Pi OS, Ubuntu) |

## Python Dependencies

```toml
# From pyproject.toml
dependencies = [
  "flask>=3.0.0",
  "requests>=2.31.0",
  "werkzeug>=3.0.0",
]
```

## Optional AI Dependencies

| Model | Size | Purpose |
|-------|------|---------|
| qwen2.5:7b-instruct | ~4.7GB | Primary AI model |
| llama3 | ~4.3GB | Alternative model |
| nomic-embed-text | ~100MB | Embeddings |
