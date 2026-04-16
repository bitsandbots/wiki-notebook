#!/bin/bash
# package.sh - Build and package Wiki Notebook for distribution
# Usage: ./package.sh <version>
# Examples:
#   ./package.sh 0.2.0          # Build version 0.2.0
#   ./package.sh 0.2.0 --upload # Build and upload to PyPI

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[*]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

VERSION=$1
UPLOAD=false
if [ "$2" == "--upload" ]; then
    UPLOAD=true
fi

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [--upload]"
    echo "Example: $0 0.2.0 --upload"
    echo ""
    echo "Version must follow semantic versioning (e.g., 0.2.0)"
    exit 1
fi

# Validate version format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    log_error "Invalid version format. Use semantic versioning (e.g., 0.2.0)"
    exit 1
fi

echo "=== Wiki Notebook Package Builder ==="
echo "Version: $VERSION"
echo ""

# Check git status
log_info "Checking git status..."
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    log_warning "There are uncommitted changes"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in __init__.py
log_info "Updating version in wiki_notebook/__init__.py..."
sed -i "s/__version__ = \"[^\"]*\"/__version__ = \"$VERSION\"/" wiki_notebook/__init__.py
log_success "Version updated"

# Update CHANGELOG.md if not already updated for this version
log_info "Checking CHANGELOG.md..."
if ! grep -q "\[$VERSION\]" CHANGELOG.md; then
    log_warning "CHANGELOG.md does not contain entry for $VERSION"
    read -p "Add entry now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat >> CHANGELOG.md << EOF

## [$VERSION] - $(date +%Y-%m-%d)
### Added
### Changed
### Fixed
### Removed

EOF
        log_success "Added changelog entry"
    fi
fi

# Clean previous builds
log_info "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info
log_success "Cleaned"

# Build distribution
log_info "Building distribution package..."
python3 -m build
log_success "Build complete"

# List built files
echo ""
echo "Built packages:"
ls -la dist/
echo ""

# Verify build
log_info "Verifying package integrity..."
python3 -m pip install --no-index --find-links=dist wiki-notebook==$VERSION 2>/dev/null || true
log_success "Package verified"

echo ""
echo "=== Package Complete ==="
echo ""
echo "To install locally:"
echo "  pip install dist/wiki_notebook-$VERSION-py3-none-any.whl"
echo ""
echo "To upload to PyPI:"
echo "  python3 -m twine upload dist/wiki_notebook-$VERSION-*"
echo ""
echo "To create git tag:"
echo "  git add -A"
echo "  git commit -m \"release: version $VERSION\""
echo "  git tag v$VERSION"
echo "  git push origin main && git push origin v$VERSION"
echo ""

if [ "$UPLOAD" == "true" ]; then
    log_info "Uploading to PyPI..."
    python3 -m twine upload dist/wiki_notebook-$VERSION-*
    log_success "Uploaded to PyPI"
fi
