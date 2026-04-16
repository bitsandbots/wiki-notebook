# Wiki Notebook Installation Guide

This guide covers installing Wiki Notebook on a Raspberry Pi or similar Linux system.

## Prerequisites

- Raspberry Pi 4/5 with 4GB+ RAM
- Raspberry Pi OS (Bookworm) or Ubuntu 22.04+
- Python 3.10 or higher
- Ollama installed and running

## Installation Steps

### 1. Install Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip sqlite3

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Clone or Copy the Project

```bash
# Option A: From Git
git clone https://github.com/coreconduit/wiki-notebook.git
cd wiki-notebook

# Option B: Copy from existing installation
# Copy the entire wiki-notebook directory
```

### 3. Install Python Dependencies

```bash
pip3 install -e .
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your preferences
# See .env.example for configuration options
```

### 5. Initialize the Database

```bash
python -m wiki_notebook init
```

### 6. Test the Installation

```bash
python -m wiki_notebook
```

Visit `http://localhost:5000/` to verify.

### 7. (Optional) Enable Systemd Service

```bash
# Copy service file
sudo cp systemd/wiki-notebook.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable wiki-notebook

# Start the service
sudo systemctl start wiki-notebook

# Check status
sudo systemctl status wiki-notebook
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BIND_HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `5000` | Server port |
| `DB_PATH` | `data/notebook.db` | SQLite database path |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Model for AI features |
| `OLLAMA_TIMEOUT` | `30` | Ollama request timeout (seconds) |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Save note |
| `/` | Focus search |
| `Esc` | Close editor / reset |
| `Shift+Click` | Multi-select notes |

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :5000

# Change PORT in .env or kill the process
```

### Ollama Connection Failed

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
sudo systemctl restart ollama
```

### Permission Errors

```bash
# Ensure correct ownership
sudo chown -R www-data:www-data /var/lib/wiki-notebook
sudo chown -R www-data:www-data /var/www/wiki-notebook
```

## Uninstallation

```bash
# Stop and disable systemd service
sudo systemctl stop wiki-notebook
sudo systemctl disable wiki-notebook

# Remove service file
sudo rm /etc/systemd/system/wiki-notebook.service
sudo systemctl daemon-reload

# Remove the project directory
rm -rf /path/to/wiki-notebook
```

## Support

- GitHub: https://github.com/coreconduit/wiki-notebook
- Issues: https://github.com/coreconduit/wiki-notebook/issues
