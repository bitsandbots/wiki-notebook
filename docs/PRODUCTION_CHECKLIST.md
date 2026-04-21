# Wiki Notebook Production Readiness Checklist

Use this checklist to prepare for production deployment on Raspberry Pi or Linux server.

## Pre-Deployment Verification (Local)

- [ ] **Tests Pass**: Run `pytest` — expect 143/143 passing
- [ ] **Code Quality**: No warnings from linters
- [ ] **Security**: Run `black --check`, `isort --check`
- [ ] **Feature Test**: Create note, categorize, verify confidence & suggestions
- [ ] **Git Clean**: `git status` shows clean working tree

## System Preparation (Raspberry Pi / Linux)

### Hardware & OS
- [ ] Raspberry Pi 5 8GB or equivalent system ready
- [ ] Latest OS installed (Raspberry Pi OS, Ubuntu 20.04+, Debian 11+)
- [ ] System updates applied: `sudo apt update && sudo apt upgrade -y`
- [ ] Ollama installed and running: `curl http://localhost:11434/api/tags`
- [ ] At least 500MB free disk space
- [ ] At least 512MB free RAM

### User & Directories
- [ ] Dedicated user created: `sudo useradd -r -s /bin/false -d /opt/wiki-notebook wiki-notebook`
- [ ] Application directory exists: `/opt/wiki-notebook`
- [ ] Data directory created: `/opt/wiki-notebook/data`
- [ ] Permissions set: `sudo chown -R wiki-notebook:wiki-notebook /opt/wiki-notebook`

### Python Environment
- [ ] Python 3.11+ installed: `python3 --version`
- [ ] Virtual environment created: `python3 -m venv /opt/wiki-notebook/.venv`
- [ ] Dependencies installed: `pip install -e .`
- [ ] Database initialized: `python scripts/init_db.py`

## Configuration

### Environment Variables
- [ ] `OLLAMA_URL` set (default: `http://localhost:11434`)
- [ ] `OLLAMA_MODEL` set (default: `qwen2.5:7b-instruct`)
- [ ] Optional: `WIKI_NOTE_CATEGORIES` for custom categories
- [ ] Config file created: `/etc/wiki-notebook/config.env`
- [ ] Permissions set: `sudo chmod 600 /etc/wiki-notebook/config.env`

### Systemd Service
- [ ] Service file copied: `sudo cp .github/wiki-notebook.service /etc/systemd/system/`
- [ ] Service file verified: `sudo systemd-analyze verify /etc/systemd/system/wiki-notebook.service`
- [ ] Daemon reloaded: `sudo systemctl daemon-reload`
- [ ] Service enabled: `sudo systemctl enable wiki-notebook`

## Deployment

### Start Service
- [ ] Service started: `sudo systemctl start wiki-notebook`
- [ ] Service status good: `sudo systemctl status wiki-notebook`
- [ ] No errors in logs: `sudo journalctl -u wiki-notebook -n 20`

### Functional Tests
- [ ] Health endpoint works: `curl http://localhost:5000/api/health | jq .`
- [ ] DB reachable: Health check shows `"db": {"ok": true}`
- [ ] Ollama reachable: Health check shows `"ollama": {"reachable": true}`
- [ ] Queue empty: Health check shows `"enrichment_queue_size": 0`

### Feature Tests
- [ ] Create note via API: `curl -X POST http://localhost:5000/api/notes ...`
- [ ] List notes: `curl http://localhost:5000/api/notes`
- [ ] Categorize note: `curl -X POST http://localhost:5000/api/notes/1/categorize`
- [ ] Response includes `confidence` and `suggestions` fields
- [ ] Search works: `curl http://localhost:5000/api/search?q=test`

## Security Hardening

### File Permissions
- [ ] Database owned by wiki-notebook user: `ls -la /opt/wiki-notebook/data/`
- [ ] Config file restricted: `ls -la /etc/wiki-notebook/config.env` shows `600`
- [ ] Virtual environment in /opt: `ls /opt/wiki-notebook/.venv/`

### Firewall
- [ ] Firewall allows port 5000 (if remote access needed):
  ```bash
  sudo ufw allow 5000/tcp
  # Or restrict to local only:
  sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 5000
  ```
- [ ] Ollama port 11434 is local-only (not exposed to internet)

### Service Security
- [ ] Service runs as unprivileged user: `ps aux | grep wiki-notebook`
- [ ] ProtectSystem=strict active in systemd service
- [ ] ProtectHome=true active in systemd service

## Monitoring & Logging

### Logs
- [ ] Journalctl integration working: `sudo journalctl -u wiki-notebook -f`
- [ ] Logs persist across restarts: `sudo journalctl -u wiki-notebook --boot`
- [ ] No ERROR level logs: `sudo journalctl -u wiki-notebook -p err`

### Health Checks
- [ ] Set up automated health monitoring:
  ```bash
  # Add to crontab (run every 5 minutes)
  */5 * * * * curl -s http://localhost:5000/api/health > /dev/null || systemctl restart wiki-notebook
  ```
- [ ] Monitor queue size: `curl http://localhost:5000/api/health | jq .enrichment_queue_size`

### Performance
- [ ] Response time acceptable: Create note, time the response
- [ ] CPU usage normal: `top` or `htop` (should be idle when not processing)
- [ ] Memory usage reasonable: Under 150MB base, peaks during categorization

## Backup & Disaster Recovery

### Database Backups
- [ ] Backup script created:
  ```bash
  sudo cp /opt/wiki-notebook/data/notebook.db /backup/notebook-$(date +%Y%m%d-%H%M%S).db
  ```
- [ ] Automated backups scheduled (daily):
  ```bash
  0 2 * * * sudo cp /opt/wiki-notebook/data/notebook.db /backup/notebook-$(date +\%Y\%m\%d).db
  ```
- [ ] Backup retention policy set (keep last 30 days)
- [ ] Test restore process once

### Disaster Recovery
- [ ] Restore procedure documented
- [ ] Backup location tested (can be restored to new system)

## Post-Deployment

### Documentation
- [ ] Deployment notes recorded (date, version, configuration)
- [ ] Custom categories documented (if used)
- [ ] Admin contacts listed
- [ ] Escalation procedure documented

### Handover
- [ ] Team trained on service management
- [ ] On-call runbook created
- [ ] Common issues documented

## Final Checklist

- [ ] All tests passing
- [ ] All checklist items completed
- [ ] Service running and healthy
- [ ] Monitoring active
- [ ] Backups working
- [ ] Documentation complete
- [ ] **READY FOR PRODUCTION** ✅

---

## Rollback Plan

If issues occur post-deployment:

1. **Stop service**: `sudo systemctl stop wiki-notebook`
2. **Restore backup**: `sudo cp /backup/notebook-YYYYMMDD.db /opt/wiki-notebook/data/notebook.db`
3. **Restart service**: `sudo systemctl start wiki-notebook`
4. **Verify**: `curl http://localhost:5000/api/health`

Rollback takes <5 minutes. Keep backups for at least 30 days.
