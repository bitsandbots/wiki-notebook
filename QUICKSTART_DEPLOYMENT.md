# Wiki Notebook — Quick Start Deployment

**Goal:** Get Wiki Notebook running in 15 minutes on Raspberry Pi or Linux server.

## Prerequisites

- Raspberry Pi 5 (or Linux system) with Raspberry Pi OS
- Ollama running: `curl http://localhost:11434/api/tags`
- `sudo` access
- Git installed

## 1. One-Liner Setup (Recommended)

```bash
curl -sS https://install.wiki-notebook.coreconduit.com | bash
```

This does everything in one command. Skip to step 4.

## 2. Manual Setup (If One-Liner Not Available)

### Clone & Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/bitsandbots/wiki-notebook.git /opt/wiki-notebook
cd /opt/wiki-notebook

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Initialize database
python scripts/init_db.py
```

### Create Service User (1 minute)

```bash
# Create unprivileged user
sudo useradd -r -s /bin/false -d /opt/wiki-notebook wiki-notebook

# Set permissions
sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook
```

### Install Systemd Service (1 minute)

```bash
# Copy service file
sudo cp .github/wiki-notebook.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable wiki-notebook
sudo systemctl start wiki-notebook
```

## 3. Verify Installation (2 minutes)

```bash
# Check service status
sudo systemctl status wiki-notebook

# View logs (should show "Running on http://127.0.0.1:5000")
sudo journalctl -u wiki-notebook -n 10

# Test health endpoint
curl http://localhost:5000/api/health | jq .

# Expected output shows:
# - "db": {"ok": true}
# - "ollama": {"reachable": true}
# - "enrichment_queue_size": 0
```

## 4. Test the Feature (3 minutes)

### Create a Note

```bash
curl -X POST http://localhost:5000/api/notes \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Team Meeting",
    "body": "Discussed Q2 roadmap and timeline"
  }'
```

### Categorize It

```bash
curl -X POST http://localhost:5000/api/notes/1/categorize

# Response includes:
# - "category": "meetings"
# - "confidence": 85 (for AI) or 0-100 (for keyword match)
# - "suggestions": [...top 3 alternatives...]
# - "tags": ["meeting", "discussed", ...]
```

### View All Notes

```bash
curl http://localhost:5000/api/notes | jq .
```

## 5. Optional: Configure Custom Categories

```bash
# Create config directory
sudo mkdir -p /etc/wiki-notebook

# Add custom categories
sudo tee /etc/wiki-notebook/config.env > /dev/null <<EOF
WIKI_NOTE_CATEGORIES='{"custom": ["keyword1", "keyword2"], "research": ["study", "article"]}'
EOF

# Secure the config
sudo chmod 600 /etc/wiki-notebook/config.env
sudo chown wiki-notebook:wiki-notebook /etc/wiki-notebook/config.env

# Restart service to load config
sudo systemctl restart wiki-notebook
```

## 6. Monitor the Service

### Watch Logs in Real-Time

```bash
sudo journalctl -u wiki-notebook -f
```

### Check Service Health

```bash
# Every 5 minutes
watch -n 5 'curl -s http://localhost:5000/api/health | jq .'
```

### View Service Status

```bash
sudo systemctl status wiki-notebook
```

## 7. Manage the Service

### Restart

```bash
sudo systemctl restart wiki-notebook
```

### Stop

```bash
sudo systemctl stop wiki-notebook
```

### Check Logs (Last 50 lines)

```bash
sudo journalctl -u wiki-notebook -n 50
```

### View Errors Only

```bash
sudo journalctl -u wiki-notebook -p err
```

## Troubleshooting

### Service Won't Start

```bash
# Check detailed error logs
sudo journalctl -u wiki-notebook -p err -n 20

# Verify systemd service syntax
sudo systemd-analyze verify /etc/systemd/system/wiki-notebook.service

# Check database permissions
ls -la /opt/wiki-notebook/data/

# Ensure Ollama is running
curl http://localhost:11434/api/tags
```

### High CPU Usage

```bash
# Check queue depth
curl http://localhost:5000/api/health | jq .enrichment_queue_size

# If queue is large, Ollama may be slow
# Try restarting Ollama:
sudo systemctl restart ollama
```

### Can't Access from Another Machine

The service binds to localhost (127.0.0.1) by default for security. To access remotely:

**Option 1: Use SSH Tunnel (Recommended)**

```bash
ssh -L 5000:localhost:5000 user@raspberry-pi.local
# Then access at http://localhost:5000 locally
```

**Option 2: Use Reverse Proxy (nginx)**

```bash
# Install nginx
sudo apt install nginx

# Create /etc/nginx/sites-available/wiki-notebook:
sudo tee /etc/nginx/sites-available/wiki-notebook > /dev/null <<'EOF'
server {
    listen 80;
    server_name wiki-notebook.local;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/wiki-notebook /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## Backup Your Data

```bash
# Backup database
sudo cp /opt/wiki-notebook/data/notebook.db ~/notebook-backup-$(date +%Y%m%d).db

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * sudo cp /opt/wiki-notebook/data/notebook.db ~/notebook-backup-\$(date +\%Y\%m\%d).db") | crontab -
```

## Next Steps

- **Read Full Documentation**: See `docs/DEPLOYMENT.md` for detailed setup
- **Production Checklist**: Review `docs/PRODUCTION_CHECKLIST.md` before going live
- **Custom Configuration**: Check `CLAUDE.md` for environment variables
- **Contribute**: Star the repo at [github.com/bitsandbots/wiki-notebook](https://github.com/bitsandbots/wiki-notebook)

---

**That's it! Your Wiki Notebook is now running.** 🚀

Access it at `http://localhost:5000` (or via SSH tunnel/reverse proxy from remote machines).
