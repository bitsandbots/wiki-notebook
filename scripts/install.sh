#!/bin/bash
# install.sh - Installation script for Wiki Notebook
# Usage: curl -sS https://install.wiki-notebook.coreconduit.com | bash
#        or run directly: bash install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "=== Wiki Notebook Installer ==="
echo ""

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    log_error "Python 3.11 or higher is required"
    echo "Found Python $PYTHON_VERSION"
    exit 1
fi
log_success "Python $PYTHON_VERSION found"

# Check SQLite with FTS5
log_info "Checking SQLite FTS5 support..."
if ! python3 -c 'import sqlite3; conn = sqlite3.connect(":memory:"); conn.execute("CREATE VIRTUAL TABLE test USING fts5(content)")' 2>/dev/null; then
    log_error "SQLite with FTS5 support is required"
    echo "Install: sudo apt install sqlite3 libsqlite3-dev"
    exit 1
fi
log_success "SQLite FTS5 supported"

# Check Ollama (optional)
log_info "Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    log_warning "Ollama not found"
    echo "Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "AI features will not be available"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    OLLAMA_VERSION=$(ollama --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Ollama $OLLAMA_VERSION found"
fi

# Create project directory
log_info "Creating project directory..."
PROJECT_DIR="${HOME}/wiki-notebook"

# Check if running in project directory
if [ -f "${PWD}/pyproject.toml" ]; then
    PROJECT_DIR="${PWD}"
    log_success "Detected local project directory: $PROJECT_DIR"
else
    if [ -d "$PROJECT_DIR" ]; then
        log_warning "Project directory already exists: $PROJECT_DIR"
        read -p "Overwrite? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        rm -rf "$PROJECT_DIR"
    fi
    mkdir -p "$PROJECT_DIR"
fi

# Clone or copy repository if needed
if [ "${PWD}" != "$PROJECT_DIR" ]; then
    log_info "Copying files to $PROJECT_DIR..."
    cp -r "${PWD}"/* "$PROJECT_DIR/" 2>/dev/null || true
    cp -r "${PWD}"/.* "$PROJECT_DIR/" 2>/dev/null || true
    log_success "Files copied"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Create virtual environment if needed
log_info "Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
log_info "Installing dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"
log_success "Dependencies installed"

# Initialize database
log_info "Initializing database..."
python scripts/init_db.py
log_success "Database initialized"

# Create environment file if it doesn't exist
log_info "Creating configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success "Created .env with default settings"
    else
        # Create minimal .env
        cat > .env << 'EOF'
BIND_HOST=127.0.0.1
PORT=5000
DB_PATH=./data/notebook.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_TIMEOUT=30
EOF
        log_success "Created .env with default settings"
    fi
else
    log_info ".env already exists"
fi

# Show setup instructions
echo ""
echo "=== Installation Complete ==="
echo ""
echo "Configuration: $PROJECT_DIR/.env"
echo "Database: $PROJECT_DIR/data/notebook.db"
echo ""
echo "To start the server:"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  python -m wiki_notebook"
echo ""
echo "Then open http://localhost:5000/"
echo ""

# Check for systemd service
if [ -f "systemd/wiki-notebook.service" ]; then
    echo "To run as a system service (optional):"
    echo "  sudo cp systemd/wiki-notebook.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable wiki-notebook"
    echo "  sudo systemctl start wiki-notebook"
    echo ""
fi

echo -e "${GREEN}Ready to go!${NC}"
