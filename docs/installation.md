# Installation Guide - Wiki Notebook

## Prerequisites

### Required

- **Python 3.11+** — Check with `python3 --version`
- **SQLite with FTS5** — Most modern Linux distros include this
- **Linux** — Raspberry Pi OS Bookworm, Ubuntu 22.04+, Debian 11+

### Recommended

- **Raspberry Pi 4/5** — 4GB+ RAM for AI features
- **Ollama** — For AI categorization, optimization, and title suggestions

## Installation Methods

### Method 1: One-Liner (Recommended)

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

Installs to `~/wiki-notebook` with a Python virtual environment. No root required.

### Method 2: One-Liner with systemd Service

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash -s -- --systemd
```

Creates a `wiki-notebook` system user, installs to `/opt/wiki-notebook`, and enables the systemd service to start on boot.

### Method 3: Manual Installation

#### 1. Clone and Set Up

```bash
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### 2. Configure

```bash
# Edit .env with your preferences (created automatically on first run)
cp .env.example .env 2>/dev/null || true
```

Example `.env`:

```env
BIND_HOST=127.0.0.1
PORT=5000
DB_PATH=./data/notebook.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=30
```

#### 3. Initialize Database

```bash
python scripts/init_db.py
```

#### 4. Start

```bash
python -m wiki_notebook
```

Visit `http://localhost:5000/`.

## Production Setup with systemd

### Automated (Recommended)

```bash
bash scripts/install.sh --systemd --install-dir /opt/wiki-notebook
```

This handles user creation, permissions, venv, database init, and service enablement in one step.

### Manual systemd Setup

#### 1. Create System User

```bash
sudo useradd --system --no-create-home \
    --home-dir /opt/wiki-notebook \
    --shell /usr/sbin/nologin \
    wiki-notebook
```

#### 2. Install Application

```bash
sudo mkdir -p /opt/wiki-notebook
sudo cp -a . /opt/wiki-notebook
sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook
cd /opt/wiki-notebook
sudo -u wiki-notebook python3 -m venv .venv
sudo -u wiki-notebook .venv/bin/pip install -e .
sudo -u wiki-notebook .venv/bin/python scripts/init_db.py
```

#### 3. Install Service

```bash
sudo cp systemd/wiki-notebook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wiki-notebook
sudo systemctl start wiki-notebook
```

#### 4. Verify

```bash
sudo systemctl status wiki-notebook
sudo journalctl -u wiki-notebook -f
curl http://localhost:5000/api/health
```

## Post-Installation

### Test the API

```bash
# Health check
curl http://localhost:5000/api/health

# Create a test note
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","body":"Wiki Notebook is running!"}'
```

### Configure Ollama (Optional)

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull a model
ollama pull qwen2.5:7b-instruct
```

## Updating

### Manual Install

```bash
cd wiki-notebook
git pull
source .venv/bin/activate
pip install -e .
python scripts/init_db.py  # apply any schema changes
```

### systemd Install

```bash
cd /opt/wiki-notebook
sudo systemctl stop wiki-notebook
sudo -u wiki-notebook git pull origin main
sudo -u wiki-notebook .venv/bin/pip install -e .
sudo -u wiki-notebook .venv/bin/python scripts/init_db.py
sudo systemctl start wiki-notebook
```

## Uninstallation

### Manual Install

```bash
pkill -f "python -m wiki_notebook"
rm -rf /path/to/wiki-notebook
```

### systemd Install

```bash
sudo systemctl stop wiki-notebook
sudo systemctl disable wiki-notebook
sudo rm /etc/systemd/system/wiki-notebook.service
sudo systemctl daemon-reload
sudo userdel wiki-notebook
sudo rm -rf /opt/wiki-notebook
```

## Troubleshooting

### Port Already in Use

```bash
sudo lsof -i :5000
# Change PORT in .env or kill the conflicting process
```

### FTS5 Not Available

```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
# Raspberry Pi: sudo apt install sqlite3 libsqlite3-dev
```

### Ollama Connection Failed

```bash
sudo systemctl restart ollama
sudo journalctl -u ollama -f
```

### Permission Errors (systemd)

```bash
sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook
```

### Service Won't Start

```bash
sudo journalctl -u wiki-notebook -n 50 --priority err
sudo systemd-analyze verify /etc/systemd/system/wiki-notebook.service
```

## Support

- **Repo**: https://github.com/coreconduit/wiki-notebook
- **Issues**: https://github.com/coreconduit/wiki-notebook/issues
- **Docs**: https://github.com/coreconduit/wiki-notebook/tree/main/docs
