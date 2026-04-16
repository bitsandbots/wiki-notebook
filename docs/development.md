# Developer Guide - Wiki Notebook

## Development Setup

### Prerequisites

- Python 3.11+
- Virtual environment
- SQLite with FTS5

### Installation for Development

```bash
# Clone repository
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_notes_crud.py

# Run with coverage
pytest --cov=wiki_notebook --cov-report=html

# Run tests with verbose output
pytest -v
```

### Running the Application

```bash
# Development server
python -m wiki_notebook

# Production server (with gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 wiki_notebook.__main__:app
```

## Code Style

### Python

- **Format**: Black (88 char lines)
- **Imports**: isort (standard library, third-party, local)
- **Type Hints**: Required on all functions
- **Docstrings**: Google style

### JavaScript

- **Format**: Prettier
- **ESLint**: Recommended

### CSS

- **Format**: Prettier
- **Naming**: BEM-style class names

## Project Structure

```
wiki-notebook/
├── wiki_notebook/          # Core package
│   ├── __init__.py
│   ├── __main__.py        # CLI entry point
│   ├── app.py             # Flask factory
│   ├── config.py          # Configuration
│   ├── db.py              # Database helpers
│   ├── models.py          # Data models
│   ├── validation.py      # Input validation
│   ├── repository.py      # Data access layer
│   ├── search.py          # FTS5 search
│   ├── routes/            # API routes
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── notes.py
│   │   └── search.py
│   └── ai/                # AI integration
│       ├── __init__.py
│       ├── ollama_client.py
│       ├── categorize.py
│       └── worker.py
├── static/                # Frontend assets
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── vendor/            # Third-party JS
├── tests/                 # Test suite
│   ├── conftest.py
│   ├── test_notes_crud.py
│   ├── test_search.py
│   ├── test_categorize.py
│   ├── test_combine.py
│   └── test_optimize.py
├── scripts/               # Utility scripts
│   ├── init_db.py
│   └── rebuild_fts.py
├── docs/                  # Documentation
├── systemd/               # Service files
└── LICENSE
```

## Adding New Features

1. **Add test first** - Write test in `tests/` directory
2. **Implement feature** - Add code following project patterns
3. **Run tests** - `pytest` to verify
4. **Update docs** - Document new API endpoints
5. **Update TRACKING.md** - Mark session as complete

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIND_HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `5000` | Server port |
| `DB_PATH` | `data/notebook.db` | SQLite database path |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Model for AI features |
| `OLLAMA_TIMEOUT` | `30` | Request timeout in seconds |

## Debugging

### Enable Flask Debug Mode

```bash
FLASK_DEBUG=1 python -m wiki_notebook
```

### View Database

```bash
sqlite3 data/notebook.db
# Commands: .tables, .schema, SELECT * FROM notes;
```

### Ollama Debug

```bash
# Check Ollama logs
ollama logs

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## Release Process

```bash
# 1. Update version in wiki_notebook/__init__.py
# 2. Update CHANGELOG.md
# 3. Run tests
pytest

# 4. Build distribution
python -m build

# 5. Tag release
git tag v0.2.0
git push origin v0.2.0
```

## Troubleshooting

### Tests Failing

```bash
# Clear cache
pytest --clear-cache

# Reinstall
pip install -e .
```

### Database Issues

```bash
# Rebuild database
rm data/notebook.db
python scripts/init_db.py
```

### Import Errors

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Reinstall
pip install -e .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- GitHub: https://github.com/coreconduit/wiki-notebook
- Issues: https://github.com/coreconduit/wiki-notebook/issues
