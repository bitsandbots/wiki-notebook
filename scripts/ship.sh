#!/bin/bash
# ship.sh — Release workflow for Wiki Notebook
# Usage: ./scripts/ship.sh <version> [options]
#
# Options:
#   --dry-run       Show what would be done, make no changes
#   --deploy        Print deployment steps after tagging
#   --skip-tests    Skip pytest (not recommended)
#   --skip-package  Skip dist/ build

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[*]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error()   { echo -e "${RED}[✗]${NC} $1"; }

VERSION=""
DRY_RUN=false
DEPLOY=false
SKIP_TESTS=false
SKIP_PACKAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)      DRY_RUN=true;      shift ;;
        --deploy)       DEPLOY=true;       shift ;;
        --skip-tests)   SKIP_TESTS=true;   shift ;;
        --skip-package) SKIP_PACKAGE=true; shift ;;
        *) [ -z "$VERSION" ] && VERSION="$1"; shift ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [--dry-run] [--deploy] [--skip-tests] [--skip-package]"
    echo "Example: $0 0.3.0"
    exit 1
fi

if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    log_error "Version must be semver (e.g. 0.3.0)"
    exit 1
fi

CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "unknown")
echo "=== Wiki Notebook Ship Workflow ==="
echo "Version : $VERSION"
echo "Branch  : $CURRENT_BRANCH"
echo "Dry-run : $DRY_RUN"
echo ""

# ── Step 1: git status ─────────────────────────────────────────────────────
log_info "Step 1/6: Checking git status…"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    log_warning "Uncommitted changes present"
    if [ "$DRY_RUN" != "true" ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r; echo
        [[ $REPLY =~ ^[Yy]$ ]] || exit 1
    fi
else
    log_success "Working tree is clean"
fi

# ── Step 2: Tests ──────────────────────────────────────────────────────────
if [ "$SKIP_TESTS" != "true" ]; then
    log_info "Step 2/6: Running test suite…"
    if [ "$DRY_RUN" == "true" ]; then
        echo "  pytest -q"
        log_success "(dry-run) tests would run"
    else
        if pytest -q; then
            log_success "All tests passed"
        else
            log_error "Tests failed — aborting"
            exit 1
        fi
    fi
else
    log_warning "Step 2/6: Tests skipped (--skip-tests)"
fi

# ── Step 3: Version consistency check ─────────────────────────────────────
log_info "Step 3/6: Checking version consistency…"
INIT_VER=$(grep -oE '[0-9]+\.[0-9]+\.[0-9]+' wiki_notebook/__init__.py | head -1)
PYPROJECT_VER=$(grep -oE 'version = "[0-9]+\.[0-9]+\.[0-9]+"' pyproject.toml | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
if [ "$INIT_VER" != "$VERSION" ] || [ "$PYPROJECT_VER" != "$VERSION" ]; then
    if [ "$DRY_RUN" == "true" ]; then
        log_warning "__init__.py=$INIT_VER  pyproject.toml=$PYPROJECT_VER  target=$VERSION"
        log_warning "(dry-run) Would update versions"
    else
        sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/" wiki_notebook/__init__.py
        sed -i "s/^version = \"[^\"]*\"/version = \"$VERSION\"/" pyproject.toml
        log_success "Version updated to $VERSION in __init__.py and pyproject.toml"
    fi
else
    log_success "Version $VERSION consistent in __init__.py and pyproject.toml"
fi

# ── Step 4: CHANGELOG ─────────────────────────────────────────────────────
log_info "Step 4/6: Checking CHANGELOG…"
if grep -q "\[$VERSION\]" CHANGELOG.md; then
    log_success "CHANGELOG already has [$VERSION] entry"
else
    if [ "$DRY_RUN" == "true" ]; then
        log_warning "(dry-run) Would add skeleton CHANGELOG entry for $VERSION"
    else
        DATE=$(date +%Y-%m-%d)
        # Insert after [Unreleased] section
        sed -i "/^## \[Unreleased\]/a \\
\\
## [$VERSION] - $DATE\\
### Added\\
### Changed\\
### Fixed" CHANGELOG.md
        log_success "Added CHANGELOG skeleton entry for $VERSION"
    fi
fi

# ── Step 5: Build package ──────────────────────────────────────────────────
if [ "$SKIP_PACKAGE" != "true" ]; then
    log_info "Step 5/6: Building distribution package…"
    if [ "$DRY_RUN" == "true" ]; then
        echo "  python3 -m build → dist/"
        log_success "(dry-run) Package build would run"
    else
        rm -rf dist/ build/ *.egg-info
        python3 -m build
        # Verify artifacts
        WHL=$(ls dist/*.whl 2>/dev/null | head -1)
        TGZ=$(ls dist/*.tar.gz 2>/dev/null | head -1)
        if [ -z "$WHL" ] || [ -z "$TGZ" ]; then
            log_error "Build artifacts not found in dist/"
            exit 1
        fi
        # Check package metadata
        if command -v twine &>/dev/null; then
            twine check dist/*
            log_success "Twine metadata check passed"
        fi
        log_success "Package built: $(basename "$WHL") + $(basename "$TGZ")"
    fi
else
    log_warning "Step 5/6: Package build skipped (--skip-package)"
fi

# ── Step 6: Commit and tag ─────────────────────────────────────────────────
log_info "Step 6/6: Creating release commit and tag…"
if git tag -l | grep -q "^v${VERSION}$"; then
    log_warning "Tag v$VERSION already exists — skipping tag creation"
elif [ "$DRY_RUN" == "true" ]; then
    echo "  git add -u  # staged + tracked modifications"
    echo "  git commit -m 'release: v$VERSION'"
    echo "  git tag v$VERSION"
    log_success "(dry-run) Commit and tag would be created"
else
    git add -u  # staged + tracked modifications only
    git commit -m "release: v$VERSION"
    git tag "v$VERSION"
    log_success "Commit: $(git rev-parse --short HEAD)  Tag: v$VERSION"
fi

echo ""
echo "=== Ship Workflow Complete ==="
echo ""
echo "Push to GitHub:"
echo "  git push origin ${CURRENT_BRANCH} && git push origin v$VERSION"
echo ""

if [ "$DEPLOY" == "true" ]; then
    echo "Deploy to server:"
    echo "  ssh user@server 'cd /opt/wiki-notebook && sudo systemctl stop wiki-notebook && sudo -u wiki-notebook git pull && sudo -u wiki-notebook .venv/bin/pip install -e . && sudo systemctl start wiki-notebook'"
    echo ""
fi

log_success "v$VERSION is ready."
