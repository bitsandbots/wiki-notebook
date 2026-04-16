# Troubleshooting - Wiki Notebook

Common issues and solutions when running Wiki Notebook.

## Installation Issues

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :5000

# Kill it or change PORT in .env
```

### FTS5 Not Available

```bash
# Check SQLite FTS5 support
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"

# On Raspberry Pi, ensure full SQLite version:
sudo apt install sqlite3 libsqlite3-dev
```

### Ollama Connection Failed

```bash
# Restart Ollama
sudo systemctl restart ollama

# Check logs
sudo journalctl -u ollama -f
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/lib/wiki-notebook
sudo chown -R www-data:www-data /var/www/wiki-notebook
```

## Runtime Issues

### Server Won't Start

```bash
# Check for errors
python -m wiki_notebook

# Verify database exists
ls -la data/notebook.db
```

### Search Not Working

```bash
# Rebuild FTS index
python scripts/rebuild_fts.py

# Verify FTS5 is enabled
sqlite3 data/notebook.db "SELECT * FROM notes_fts LIMIT 1;"
```

### AI Features Not Working

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull the model if needed
ollama pull qwen2.5:7b-instruct
```

## Database Issues

### Database Corruption

```bash
# Backup current database
cp data/notebook.db data/notebook.db.backup

# Reinitialize (destroys all data)
rm data/notebook.db
python scripts/init_db.py
```

### Slow Performance

```bash
# Create indexes (should be automatic from schema)
python -c "import sqlite3; conn = sqlite3.connect('data/notebook.db'); conn.execute('ANALYZE'); conn.close()"

# VACUUM to reclaim space
python -c "import sqlite3; conn = sqlite3.connect('data/notebook.db'); conn.execute('VACUUM'); conn.close()"
```

## Development Issues

### Tests Failing

```bash
# Clear cache
pytest --clear-cache

# Reinstall
pip install -e .
```

### Import Errors

```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Reinstall
pip install -e .
```

## Contribution Issues

### Code Quality Checks

```bash
# Run all tests
pytest

# Check formatting
black --check wiki_notebook/ tests/

# Check imports
isort --check-only wiki_notebook/ tests/
```

## Getting Help

- GitHub: https://github.com/coreconduit/wiki-notebook/issues
- Check existing issues before creating new ones
- Include error messages and steps to reproduce