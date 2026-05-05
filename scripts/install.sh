#!/bin/bash
# install.sh - Installation script for Wiki Notebook
# Usage:
#   curl -sS https://install.wiki-notebook.coreconduit.com | bash
#   bash install.sh
#   bash install.sh --systemd
#   bash install.sh --systemd --install-dir /opt/wiki-notebook
#
# Options:
#   --systemd        Install and enable systemd service
#   --install-dir    Custom installation directory (default: $HOME/wiki-notebook)
#   --skip-deps      Skip dependency installation

set -e

# ── Configuration ────────────────────────────────────────────────────────────
SYSTEMD=false
SKIP_DEPS=false
INSTALL_DIR="${HOME}/wiki-notebook"

while [[ $# -gt 0 ]]; do
    case $1 in
        --systemd)     SYSTEMD=true; shift ;;
        --install-dir) INSTALL_DIR="$2"; shift 2 ;;
        --skip-deps)   SKIP_DEPS=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--systemd] [--install-dir PATH] [--skip-deps]"
            exit 0 ;;
        *) shift ;;
    esac
done

# ── Output helpers ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[*]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error()   { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Wiki Notebook Installer  v0.3.0       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Install dir : $INSTALL_DIR"
echo "Systemd     : $SYSTEMD"
echo ""

# ── Pre-flight checks ───────────────────────────────────────────────────────
log_info "Checking prerequisites…"

# Python 3.11+
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    echo "Install: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    log_error "Python 3.11+ required (found $PYTHON_MAJOR.$PYTHON_MINOR)"
    exit 1
fi
log_success "Python $PYTHON_MAJOR.$PYTHON_MINOR"

# SQLite FTS5
if ! python3 -c 'import sqlite3; conn = sqlite3.connect(":memory:"); conn.execute("CREATE VIRTUAL TABLE test USING fts5(content)")' 2>/dev/null; then
    log_error "SQLite with FTS5 support required"
    echo "Install: sudo apt install sqlite3 libsqlite3-dev"
    exit 1
fi
log_success "SQLite FTS5"

# Ollama (optional)
if command -v ollama &> /dev/null; then
    OLLAMA_VER=$(ollama --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Ollama ${OLLAMA_VER:-installed}"
else
    log_warning "Ollama not found — AI features disabled"
    echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
fi

# sudo required for systemd
if [ "$SYSTEMD" = true ] && ! command -v sudo &> /dev/null; then
    log_error "--systemd requires sudo"
    exit 1
fi

echo ""

# ── Locate source ───────────────────────────────────────────────────────────
# Determine if running from repo or via curl pipe
SOURCE_DIR=""
if [ -f "${PWD}/pyproject.toml" ] && [ -f "${PWD}/scripts/init_db.py" ]; then
    SOURCE_DIR="${PWD}"
    log_info "Using local source: $SOURCE_DIR"
elif [ -d "/tmp/wiki-notebook-src" ]; then
    SOURCE_DIR="/tmp/wiki-notebook-src"
else
    log_warning "Running via curl — cloning from GitHub"
    TMPDIR=$(mktemp -d)
    git clone --depth 1 https://github.com/coreconduit/wiki-notebook.git "$TMPDIR" 2>/dev/null || {
        log_error "Cannot reach GitHub. Run from a local clone instead."
        rm -rf "$TMPDIR"
        exit 1
    }
    SOURCE_DIR="$TMPDIR"
fi

# ── Install to target directory ─────────────────────────────────────────────
if [ "${SOURCE_DIR}" != "${INSTALL_DIR}" ]; then
    log_info "Installing to $INSTALL_DIR…"

    if [ -d "$INSTALL_DIR" ]; then
        if [ "$SYSTEMD" = true ]; then
            # Don't overwrite for systemd upgrade — just rsync
            log_info "Target exists — updating files"
            rsync -a --exclude '.venv' --exclude 'data/notebook.db' --exclude '.env' \
                "${SOURCE_DIR}/" "${INSTALL_DIR}/"
        else
            log_warning "Target exists: $INSTALL_DIR"
            read -p "Overwrite? (y/N) " -n 1 -r; echo
            [[ $REPLY =~ ^[Yy]$ ]] || exit 1
            rm -rf "$INSTALL_DIR"
            cp -a "$SOURCE_DIR" "$INSTALL_DIR"
        fi
    else
        mkdir -p "$(dirname "$INSTALL_DIR")"
        cp -a "$SOURCE_DIR" "$INSTALL_DIR"
    fi
    log_success "Files installed"
fi

cd "$INSTALL_DIR"

# ── Virtual environment ─────────────────────────────────────────────────────
log_info "Setting up Python environment…"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -e "." -q
log_success "Python dependencies installed"

# ── Database ─────────────────────────────────────────────────────────────────
log_info "Initializing database…"
python scripts/init_db.py
log_success "Database ready"

# ── Configuration ────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
BIND_HOST=127.0.0.1
PORT=5000
DB_PATH=./data/notebook.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=30
EOF
    log_success "Created .env with defaults"
else
    log_info ".env exists — not overwriting"
fi

# ── Systemd installation ────────────────────────────────────────────────────
if [ "$SYSTEMD" = true ]; then
    echo ""
    log_info "Setting up systemd service…"

    SERVICE_FILE="${INSTALL_DIR}/systemd/wiki-notebook.service"

    if [ ! -f "$SERVICE_FILE" ]; then
        log_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi

    # Create system user
    if ! id -u wiki-notebook &>/dev/null; then
        sudo useradd --system --no-create-home \
            --home-dir "${INSTALL_DIR}" \
            --shell /usr/sbin/nologin \
            wiki-notebook
        log_success "Created 'wiki-notebook' system user"
    else
        log_info "System user already exists"
    fi

    # Fix ownership
    sudo chown -R wiki-notebook:wiki-notebook "${INSTALL_DIR}"

    # Copy and enable service
    sudo cp "${SERVICE_FILE}" /etc/systemd/system/wiki-notebook.service
    sudo systemctl daemon-reload
    sudo systemctl enable wiki-notebook
    sudo systemctl start wiki-notebook

    # Verify
    sleep 2
    if sudo systemctl is-active --quiet wiki-notebook; then
        log_success "Service running"
    else
        log_warning "Service may not have started — check logs:"
        echo "  sudo journalctl -u wiki-notebook -n 20"
    fi

    echo ""
    echo "Service commands:"
    echo "  sudo systemctl status wiki-notebook"
    echo "  sudo journalctl -u wiki-notebook -f"
    echo "  sudo systemctl restart wiki-notebook"
fi

# ── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "───────────────────────────────────────────"
echo -e "  ${GREEN}Installation Complete${NC}"
echo "───────────────────────────────────────────"
echo ""
echo "  URL : http://localhost:5000"
echo "  DB  : ${INSTALL_DIR}/data/notebook.db"
echo "  Env : ${INSTALL_DIR}/.env"
echo ""

if [ "$SYSTEMD" != true ]; then
    echo "To start manually:"
    echo "  cd ${INSTALL_DIR}"
    echo "  source .venv/bin/activate"
    echo "  python -m wiki_notebook"
    echo ""
    echo "To install as a service:"
    echo "  bash install.sh --systemd --install-dir ${INSTALL_DIR}"
    echo ""
fi
