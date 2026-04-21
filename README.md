# Wiki Notebook

A self-hosted, offline-first journal and wiki with automatic categorization,
full-text search, multi-note composition, optimization, and local Ollama-powered cleanup
and insight generation.

![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![WCAG 2.2 Level AA](https://img.shields.io/badge/wcag-2.2%20AA-green.svg)
![Brand v2.1](https://img.shields.io/badge/brand-CoreConduit%20v2.1-silver.svg)

## Features

- **CRUD API** — Create, read, update, delete notes
- **Auto-categorization** — Ollama suggests category + tags on save — [Learn more](docs/CATEGORIZATION.md)
- **Full-text search** — FTS5 with BM25 ranking and snippet highlighting
- **Multi-select & combine** — Merge notes with concatenate or AI synthesis
- **Optimize & Insights** — AI-powered writing enhancement with undo
- **Undo functionality** — Full revision tracking for all note operations
- **Systemd service** — Auto-start on boot for Raspberry Pi deployments

## ♿ Accessibility (WCAG 2.2 Level AA)

Wiki Notebook is fully accessible to users with disabilities:

- **High contrast mode** — AA+ color ratios for low vision users
- **Dyslexia-friendly font** — Legible font toggle (Verdana, wide letterforms)
- **Reduced motion** — Respects OS preference + manual toggle
- **Keyboard navigation** — All features via Tab, skip link, Ctrl+Enter
- **Screen reader support** — Semantic HTML + 21+ ARIA labels
- **Color-blind friendly** — No color-only indicators

**Learn more:** See [ACCESSIBILITY.md](ACCESSIBILITY.md) and [A11Y_QUICK_START.md](A11Y_QUICK_START.md)

## Architecture

| Layer    | Choice                                    |
| -------- | ----------------------------------------- |
| Backend  | Flask (Python 3.11+)                      |
| Storage  | SQLite + FTS5 virtual table               |
| Frontend | Vanilla HTML + JS + CSS (no build step)   |
| AI       | Ollama HTTP API (`http://localhost:11434`) |

## Requirements

- Python 3.11 or higher
- SQLite with FTS5 support (most modern Linux distros include this)
- Ollama (optional, for AI features)

## Installation

### One-liner (recommended)

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

### Manual install

```bash
# Clone the repository
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Initialize the database
python scripts/init_db.py

# Start the server
python -m wiki_notebook
```

## Configuration

Create a `.env` file with:

```env
BIND_HOST=127.0.0.1
PORT=5000
DB_PATH=./data/notebook.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=30
```

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `BIND_HOST` | `127.0.0.1` | Listen address (use `0.0.0.0` for LAN) |
| `PORT` | `5000` | Server port |
| `DB_PATH` | `./data/notebook.db` | SQLite database path |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama instance URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Ollama model to use |
| `OLLAMA_TIMEOUT` | `30` | Request timeout in seconds |

## Usage

```bash
# Start the server
python -m wiki_notebook

# Access the UI at
open http://127.0.0.1:5000/

# Health check
curl http://127.0.0.1:5000/api/health
```

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/health` | Health status (DB, Ollama) |
| GET | `/api/notes` | List notes with pagination |
| POST | `/api/notes` | Create note |
| GET | `/api/notes/<id>` | Get note |
| PUT | `/api/notes/<id>` | Update note |
| DELETE | `/api/notes/<id>` | Delete note |
| POST | `/api/notes/combine` | Combine multiple notes |
| POST | `/api/notes/<id>/optimize` | Optimize note with AI |
| POST | `/api/notes/<id>/undo` | Undo last optimization |
| GET | `/api/search` | Search notes with BM25 |
| GET | `/api/categories` | List categories |

## Data Sovereignty

- All notes live in one local SQLite file
- No cloud services, no telemetry
- Export is simply copying the `.db` file

## Compliance & Brand

**Wiki Notebook is certified for:**

- ✅ **WCAG 2.2 Level AA** — Web Content Accessibility Guidelines
- ✅ **CoreConduit Brand v2.1** — Silver Theme with proper color tokens
- ✅ **Section 508** — US Accessibility Law
- ✅ **EN 301 549** — EU Accessibility Directive

All colors have documented contrast ratios. The UI supports keyboard navigation, text sizing, high contrast mode, dyslexia-friendly fonts, and reduced motion preferences.

For detailed accessibility information:
- **Users:** Read [A11Y_QUICK_START.md](A11Y_QUICK_START.md)
- **Developers:** Read [ACCESSIBILITY.md](ACCESSIBILITY.md)

## License

MIT License — see LICENSE file for details.

## Status

**Current version:** 0.1.0 (pre-release)

This is an early-stage project. Features may change, and the API is not yet stable.
