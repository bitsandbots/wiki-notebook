# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wiki Notebook** is a self-hosted, offline-first journal and wiki with automatic categorization, full-text search, multi-note composition, and local Ollama-powered cleanup and insight generation.

## Commands

| Command | Purpose |
|---------|---------|
| `python -m wiki_notebook` | Start the Flask development server |
| `pytest` | Run the test suite |
| `pytest -v` | Run tests with verbose output |
| `pytest tests/test_notes_crud.py` | Run specific test file |
| `pytest --cov=wiki_notebook --cov-report=html` | Run tests with coverage |
| `python scripts/init_db.py` | Initialize the database |
| `pre-commit install` | Install pre-commit hooks |

### Development Scripts

| Script | Purpose |
|--------|---------|
| `scripts/install.sh` | One-line installation (curl-based) |
| `scripts/package.sh <version>` | Build distribution package |
| `scripts/ship.sh <version>` | Full release workflow (tests, build, commit, tag) |
| `scripts/release.sh <version>` | Legacy release script (deprecated) |

## High-Level Architecture

### Layer Structure

```
Frontend Layer (static/)
├── index.html      - Main SPA entry point
├── styles.css      - Brand v2.1 Silver theme (CoreConduit)
└── app.js          - Vanilla JS, grid-first view state machine (no build step)

Backend Layer (wiki_notebook/)
├── app.py          - Flask factory pattern
├── config.py       - Environment config (singleton)
├── db.py           - DB connection + schema bootstrap
├── repository.py   - Data access layer (CRUD)
├── models.py       - Data models (Note dataclass)
├── validation.py   - Input validation
├── search.py       - FTS5 search orchestration
├── chunking.py     - Hybrid .txt/.md chunking algorithm (import)
└── ai/             - Ollama integration
    ├── ollama_client.py
    ├── categorize.py
    └── worker.py

Routes (wiki_notebook/routes/)
├── __init__.py
├── health.py       - /api/health
├── notes.py        - /api/notes/* (CRUD + combine + optimize + import)
└── search.py       - /api/search
```

### Key Patterns

1. **Flask Factory Pattern** - `create_app()` in `app.py` configures and returns the app
2. **Repository Layer** - `repository.py` abstracts all database operations
3. **Configuration Singleton** - `config.py` loads env vars once on import
4. **Background Enrichment** - `EnrichmentWorker` processes notes async via queue
5. **FTS5 Triggers** - Schema syncs search index automatically via SQLite triggers
6. **View State Machine** - `state.view` (`"grid"` | `"detail"` | `"import-preview"`) drives `renderView()` in `app.js`

### Database Schema

- `notes` - Main table with FTS5 content
- `notes_fts` - FTS5 virtual table (porter stemmer, unicode61)
- `note_revisions` - Revision tracking for undo functionality
- Triggers: `notes_ai`, `notes_au`, `notes_ad` keep FTS5 in sync

### API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/health` | Health status (DB, Ollama) |
| GET | `/api/notes` | List notes (pagination, category filter, order) |
| POST | `/api/notes` | Create note |
| GET | `/api/notes/<id>` | Get note |
| PUT | `/api/notes/<id>` | Update note |
| DELETE | `/api/notes/<id>` | Delete note |
| POST | `/api/notes/import` | Parse uploaded .txt/.md files into chunks (no notes created) |
| POST | `/api/notes/combine` | Combine notes (concatenate or AI mode) |
| POST | `/api/notes/<id>/optimize` | Optimize note with AI |
| POST | `/api/notes/<id>/undo` | Undo last optimize |
| GET | `/api/search` | FTS5 search with BM25 ranking |
| GET | `/api/categories` | List categories |

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask 3.0+ |
| Database | SQLite with FTS5 |
| AI | Ollama HTTP API |
| Frontend | Vanilla HTML/JS/CSS (ES2021+) |
| Build | Hatch |
| Testing | pytest |

## Code Style

- **Python**: Black (88 chars), isort, type hints required
- **JavaScript**: Prettier formatting
- **CSS**: Prettier formatting
- **Commits**: Conventional format (feat:, fix:, refactor:, etc.)

## Brand Guidelines

The UI uses the **CoreConduit Brand v2.1 (Silver Theme)**:
- Dark Navy: `#0d1b2e` (topbar)
- Silver: `#d8dde8` (content background)
- Blue: `#2b7de9` (primary accent)
- Orange: `#e07018` (secondary accent)
- Fonts: Exo 2 (display), Plus Jakarta Sans (body), IBM Plex Mono (code)
- Cards: 3px gradient bar (blue→orange) on top edge

## Running the Application

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Initialize database
python scripts/init_db.py

# Start server
python -m wiki_notebook
```

### Installation (Production)

**One-liner (recommended):**
```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

**Manual installation:**
```bash
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/init_db.py
python -m wiki_notebook
```

### Release Workflow

**Full release (tests, build, commit, tag):**
```bash
./scripts/ship.sh 0.2.0
```

**Release with deployment:**
```bash
./scripts/ship.sh 0.2.0 --deploy
```

**Dry-run to see what would happen:**
```bash
./scripts/ship.sh 0.2.0 --dry-run
```

**Build only package:**
```bash
./scripts/package.sh 0.2.0
```

### Testing Release Process

1. Run ship.sh in dry-run mode first
2. Verify tests pass locally
3. Build the package and verify `dist/` contains `.whl` and `.tar.gz`
4. Push tags: `git push origin main && git push origin v0.2.0`

## Self-Hosted Deployment

For production deployment on self-hosted Linux systems, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- **System requirements** and prerequisite setup
- **Automated installation** with systemd service
- **Manual installation** with step-by-step instructions
- **Configuration** with environment variables and custom categories
- **Ollama integration** for AI-powered categorization
- **Security hardening** with firewall and HTTPS/SSL setup
- **Maintenance** including backups, updates, and monitoring
- **Troubleshooting** for common issues

Quick start for systemd deployment:
```bash
# Copy service file to systemd
sudo cp .github/wiki-notebook.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable wiki-notebook
sudo systemctl start wiki-notebook

# View logs
sudo journalctl -u wiki-notebook -f
```

## Debugging

- Enable debug mode: `FLASK_DEBUG=1 python -m wiki_notebook`
- View database: `sqlite3 data/notebook.db`
- Check Ollama: `curl http://localhost:11434/api/tags`

## Project Scripts

| File | Purpose |
|------|---------|
| `scripts/install.sh` | One-line installation script for self-hosted deployment |
| `scripts/package.sh` | Build distribution package (whl/tar.gz) |
| `scripts/ship.sh` | Complete release workflow with tests and tagging |
| `scripts/release.sh` | Legacy release script (uses ship.sh internally) |
| `scripts/init_db.py` | Database schema initialization |
| `scripts/rebuild_fts.py` | Rebuild FTS5 search index |
| `.github/workflows/release.yml` | GitHub Actions CI/CD for PyPI releases |
