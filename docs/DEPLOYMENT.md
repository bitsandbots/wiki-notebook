# Wiki Notebook Self-Hosted Deployment Guide

This guide covers production deployment of Wiki Notebook on self-hosted systems.

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, Raspberry Pi OS)
- **Python**: 3.11 or later
- **Database**: SQLite (included)
- **AI**: Ollama (optional, for categorization)
- **Disk Space**: Minimum 500MB for application + data
- **RAM**: Minimum 512MB (1GB recommended)

## Quick Start (Automated)

For automated installation with systemd setup:

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

This script will:
1. Create a dedicated `wiki-notebook` user
2. Install dependencies
3. Set up systemd service
4. Enable auto-start on boot

## Manual Installation

### 1. System Preparation

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/wiki-notebook wiki-notebook
sudo mkdir -p /opt/wiki-notebook/data
sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook
```

### 2. Install Application

```bash
# Switch to application directory
cd /opt/wiki-notebook

# Clone repository
sudo -u wiki-notebook git clone https://github.com/coreconduit/wiki-notebook.git .

# Create virtual environment
sudo -u wiki-notebook python3.11 -m venv .venv

# Activate and upgrade pip
sudo -u wiki-notebook .venv/bin/pip install --upgrade pip setuptools wheel

# Install application
sudo -u wiki-notebook .venv/bin/pip install -e .
```

### 3. Initialize Database

```bash
sudo -u wiki-notebook .venv/bin/python scripts/init_db.py
```

### 4. Configure Systemd Service

```bash
# Copy service file
sudo cp systemd/wiki-notebook.service /etc/systemd/system/

# Verify service file
sudo systemd-analyze verify /etc/systemd/system/wiki-notebook.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable wiki-notebook
sudo systemctl start wiki-notebook
```

### 5. Verify Installation

```bash
# Check service status
sudo systemctl status wiki-notebook

# View recent logs
sudo journalctl -u wiki-notebook -n 50 -f

# Test API endpoint
curl http://localhost:5000/api/health
```

## Configuration

### Environment Variables

Create `/opt/wiki-notebook/.env` if custom configuration is needed:

```bash
# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=0

# Server binding
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Custom categories (JSON)
WIKI_NOTE_CATEGORIES='{"research": ["paper", "study"], "blog": ["post", "article"]}'

# Ollama configuration (optional)
OLLAMA_API_URL=http://localhost:11434
```

Load environment variables in systemd service by adding to `/etc/systemd/system/wiki-notebook.service`:

```ini
EnvironmentFile=/opt/wiki-notebook/.env
```

### Ollama Integration (Optional)

For AI-powered categorization, install and run Ollama:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull qwen2.5-coder
```

The application will automatically detect and use Ollama when available.

## Maintenance

### Backup Database

```bash
# Manual backup
sudo -u wiki-notebook cp /opt/wiki-notebook/data/notebook.db \
  /opt/wiki-notebook/data/notebook.db.backup.$(date +%Y%m%d)

# Automated daily backup (via cron)
echo "0 2 * * * root /opt/wiki-notebook/.venv/bin/python /opt/wiki-notebook/scripts/backup.py" \
  | sudo tee /etc/cron.d/wiki-notebook-backup
```

### Update Application

```bash
sudo systemctl stop wiki-notebook

cd /opt/wiki-notebook
sudo -u wiki-notebook git pull origin main
sudo -u wiki-notebook .venv/bin/pip install -e .

# Run migrations if needed
sudo -u wiki-notebook .venv/bin/python scripts/init_db.py

sudo systemctl start wiki-notebook
```

### Monitor Service Health

```bash
# Check last 100 lines of logs
sudo journalctl -u wiki-notebook -n 100

# Follow logs in real-time
sudo journalctl -u wiki-notebook -f

# Check service restart count
sudo systemctl show wiki-notebook | grep NRestarts
```

## Troubleshooting

### Service Won't Start

Check logs for detailed error messages:

```bash
sudo journalctl -u wiki-notebook -n 50 --priority err
```

Common issues:
- **Permission denied**: Verify `/opt/wiki-notebook` ownership: `sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook`
- **Port already in use**: Change `FLASK_PORT` in `.env` file
- **Database locked**: Ensure only one instance is running: `sudo systemctl status wiki-notebook`

### Database Issues

Rebuild the FTS5 search index:

```bash
sudo -u wiki-notebook .venv/bin/python scripts/rebuild_fts.py
```

Verify database integrity:

```bash
sqlite3 /opt/wiki-notebook/data/notebook.db "PRAGMA integrity_check;"
```

### Ollama Connection Issues

Verify Ollama is running and accessible:

```bash
curl http://localhost:11434/api/tags
```

If Ollama is not accessible, the application will fall back to keyword-based categorization automatically.

## Security Hardening

### Firewall Configuration

Allow only necessary traffic:

```bash
# Allow localhost access only
sudo ufw allow from 127.0.0.1 to any port 5000

# Or restrict to specific IPs
sudo ufw allow from 192.168.1.100 to any port 5000
```

### HTTPS with Reverse Proxy

Use Nginx as a reverse proxy with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name wiki.example.com;

    ssl_certificate /etc/letsencrypt/live/wiki.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wiki.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### User Access Control

Create a system user with restricted permissions (already done in setup):

```bash
# User has no shell and limited privileges
sudo usermod -s /usr/sbin/nologin wiki-notebook

# Data directory is read-write only for the service
sudo chmod 750 /opt/wiki-notebook/data
```

## Performance Tuning

### Database Query Performance

Enable FTS5 query statistics:

```bash
sqlite3 /opt/wiki-notebook/data/notebook.db "PRAGMA optimize;"
```

Schedule regular optimization:

```bash
# Weekly optimization
echo "0 3 * * 0 wiki-notebook /opt/wiki-notebook/.venv/bin/python -c \
  \"import sqlite3; conn = sqlite3.connect('/opt/wiki-notebook/data/notebook.db'); \
   conn.execute('PRAGMA optimize;')\"" \
  | sudo tee /etc/cron.d/wiki-notebook-optimize
```

### Memory Optimization

For systems with limited RAM, reduce Python memory overhead:

Add to `.env`:

```bash
PYTHONOPTIMIZE=2
```

Or in systemd service `[Service]` section:

```ini
Environment="PYTHONOPTIMIZE=2"
```

## Monitoring

### Service Health Monitoring

Check systemd service status:

```bash
# Simple status
systemctl status wiki-notebook

# Detailed statistics
systemctl show wiki-notebook

# Auto-restart on failure (already configured)
systemctl list-dependencies --reverse wiki-notebook.timer
```

### Application Metrics

View API health and system status:

```bash
curl http://localhost:5000/api/health | jq
```

Response includes:
- Database connection status
- Ollama availability
- Note count
- System uptime

### Log Monitoring

Archive logs regularly:

```bash
# Compress old logs
sudo journalctl --vacuum=30d

# Export logs to file
sudo journalctl -u wiki-notebook -S "2 days ago" > wiki-notebook.log
```

## Uninstallation

To remove the application:

```bash
# Stop service
sudo systemctl stop wiki-notebook
sudo systemctl disable wiki-notebook

# Remove service file
sudo rm /etc/systemd/system/wiki-notebook.service
sudo systemctl daemon-reload

# Remove application and user
sudo userdel wiki-notebook
sudo rm -rf /opt/wiki-notebook
```

## Getting Help

- **Documentation**: https://github.com/coreconduit/wiki-notebook/docs
- **Issues**: https://github.com/coreconduit/wiki-notebook/issues
- **Discussions**: https://github.com/coreconduit/wiki-notebook/discussions

## License

Wiki Notebook is MIT-licensed open source software.
