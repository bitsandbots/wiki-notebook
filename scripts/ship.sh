#!/bin/bash
# ship.sh - Comprehensive release workflow for Wiki Notebook
# Usage: ./ship.sh <version>
# Examples:
#   ./ship.sh 0.2.0              # Full release flow
#   ./ship.sh 0.2.0 --dry-run    # Show what would be done
#   ./ship.sh 0.2.0 --deploy     # Build, tag, and deploy to server

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[*]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

VERSION=$1
DRY_RUN=false
DEPLOY=false
SKIP_TESTS=false
SKIP_PACKAGE=false

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --deploy)
            DEPLOY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-package)
            SKIP_PACKAGE=true
            shift
            ;;
        *)
            if [ -z "$VERSION" ]; then
                VERSION="$1"
            fi
            shift
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run       Show what would be done without making changes"
    echo "  --deploy        Deploy to production server after building"
    echo "  --skip-tests    Skip running test suite"
    echo "  --skip-package  Skip package build (use existing dist/)"
    echo ""
    echo "Example: $0 0.2.0 --deploy --skip-tests"
    exit 1
fi

# Validate version format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    log_error "Invalid version format. Use semantic versioning (e.g., 0.2.0)"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "unknown")

echo "=== Wiki Notebook Ship Workflow ==="
echo "Version: $VERSION"
echo "Branch: $CURRENT_BRANCH"
echo ""

# Step 1: Check git status
log_info "Step 1/6: Checking git status..."
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    log_warning "There are uncommitted changes"
    if [ "$DRY_RUN" == "true" ]; then
        echo "  (Would prompt to continue)"
    else
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    log_success "Git repository is clean"
fi

# Step 2: Run tests
if [ "$SKIP_TESTS" != "true" ]; then
    log_info "Step 2/6: Running test suite..."
    if [ "$DRY_RUN" == "true" ]; then
        echo "  pytest -q"
        log_success "Tests would run"
    else
        if pytest -q; then
            log_success "All tests passed"
        else
            log_error "Tests failed!"
            exit 1
        fi
    fi
else
    log_info "Step 2/6: Skipping tests (--skip-tests)"
fi

# Step 3: Update version
log_info "Step 3/6: Updating version in wiki_notebook/__init__.py..."
if [ "$DRY_RUN" == "true" ]; then
    echo "  Would update: __version__ = \"$VERSION\""
    log_success "Version update would occur"
else
    sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/" wiki_notebook/__init__.py
    log_success "Version updated to $VERSION"
fi

# Step 4: Update CHANGELOG.md
log_info "Step 4/6: Updating CHANGELOG.md..."
if [ "$DRY_RUN" == "true" ]; then
    echo "  Would add entry for $VERSION"
    log_success "Changelog update would occur"
else
    if ! grep -q "\[$VERSION\]" CHANGELOG.md; then
        cat >> CHANGELOG.md << EOF

## [$VERSION] - $(date +%Y-%m-%d)
### Added
- Multi-select functionality with checkboxes
- Combine notes endpoint (concatenate and AI modes)
- Optimize note endpoint with revision tracking
- Undo optimize endpoint

### Changed
### Fixed
### Removed

EOF
        log_success "Added changelog entry"
    else
        log_info "Changelog already updated for $VERSION"
    fi
fi

# Step 5: Build package
if [ "$SKIP_PACKAGE" != "true" ]; then
    log_info "Step 5/6: Building distribution package..."
    if [ "$DRY_RUN" == "true" ]; then
        echo "  python3 -m build"
        log_success "Package build would occur"
    else
        # Clean previous builds
        rm -rf dist/ build/ *.egg-info
        # Build
        python3 -m build
        log_success "Package built:"
        ls -la dist/
    fi
else
    log_info "Step 5/6: Skipping package build (--skip-package)"
fi

# Step 6: Commit and tag
log_info "Step 6/6: Creating release commit and tag..."
if [ "$DRY_RUN" == "true" ]; then
    echo "  git add -A"
    echo "  git commit -m \"release: version $VERSION\""
    echo "  git tag v$VERSION"
    log_success "Release commit and tag would be created"
else
    git add -A
    git commit -m "release: version $VERSION

- Update version to $VERSION
- Update CHANGELOG
- Build distribution

${VERSION}"
    git tag "v$VERSION"
    log_success "Release commit created: $(git rev-parse HEAD)"
    log_success "Git tag created: v$VERSION"
fi

echo ""
echo "=== Ship Workflow Complete ==="
echo ""
echo "Next steps:"
echo "  1. Push changes: git push origin main && git push origin v$VERSION"
echo ""

if [ "$DEPLOY" == "true" ]; then
    echo "Deployment instructions:"
    echo "  ssh user@server"
    echo "  cd /var/www/wiki-notebook"
    echo "  git pull origin main"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    echo "  python scripts/init_db.py"
    echo "  sudo systemctl restart wiki-notebook"
    echo ""
fi

log_success "Ready to deploy!"
echo ""
echo "To push and deploy:"
echo "  git push origin main && git push origin v$VERSION"
if [ "$DEPLOY" == "true" ]; then
    echo "  Then run the deployment commands above on your server"
fi
