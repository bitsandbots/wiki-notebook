# Installation Guide - Wiki Notebook

## Prerequisites

### Required

- **Python 3.11+** - Check with `python3 --version`
- **SQLite with FTS5** - Most modern Linux distros include this
- **Ollama** (optional) - For AI features

### Recommended

- **Raspberry Pi 4/5** - 4GB+ RAM
- **Linux** - Raspberry Pi OS Bookworm, Ubuntu 22.04+

## Installation Methods

### Method 1: One-Liner (Recommended)

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

### Method 2: Manual Installation

#### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Dependencies

```bash
# Python and pip
sudo apt install -y python3 python3-pip sqlite3

# Ollama (for AI features)
curl -fsSL https://ollama.com/install.sh | sh
```

#### 3. Clone the Repository

```bash
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook
```

#### 4. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 5. Install Package

```bash
pip install -e .
```

#### 6. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
nano .env
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

#### 7. Initialize Database

```bash
python -m wiki_notebook init
```

#### 8. Start the Server

```bash
python -m wiki_notebook
```

Visit `http://localhost:5000/` to verify.

### Method 3: Production Setup with systemd

#### 1. Install as System Service

```bash
# Copy service file
sudo cp systemd/wiki-notebook.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Create data directory
sudo mkdir -p /var/lib/wiki-notebook
sudo mkdir -p /var/www/wiki-notebook
sudo chown -R www-data:www-data /var/lib/wiki-notebook
sudo chown -R www-data:www-data /var/www/wiki-notebook
```

#### 2. Configure and Enable

```bash
# Copy environment file
sudo cp .env.example /etc/wiki-notebook.env

# Edit environment
sudo nano /etc/wiki-notebook.env

# Enable and start service
sudo systemctl enable wiki-notebook
sudo systemctl start wiki-notebook
```

#### 3. Check Status

```bash
sudo systemctl status wiki-notebook
sudo journalctl -u wiki-notebook -f
```

## Post-Installation

### Test Installation

```bash
# Health check
curl http://localhost:5000/api/health

# Create test note
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","body":"Test body"}'
```

### Configure Ollama (Optional)

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull model if needed
ollama pull qwen2.5:7b-instruct
```

## Troubleshooting

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

## Uninstallation

### Manual Remove

```bash
# Stop server (if running)
pkill -f "python -m wiki_notebook"

# Remove directory
rm -rf /path/to/wiki-notebook

# Remove database
rm -rf ~/.wiki-notebook
```

### systemd Remove

```bash
# Stop and disable service
sudo systemctl stop wiki-notebook
sudo systemctl disable wiki-notebook

# Remove service file
sudo rm /etc/systemd/system/wiki-notebook.service

# Reload systemd
sudo systemctl daemon-reload
```

## Updating

```bash
cd wiki-notebook
git pull
pip install -e .
python -m wiki_notebook
```

## Support

- GitHub: https://github.com/coreconduit/wiki-notebook
- Issues: https://github.com/coreconduit/wiki-notebook/issues
