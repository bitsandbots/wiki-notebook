#!/bin/bash
# release.sh - Release script for Wiki Notebook (legacy - use ship.sh)
# This script is now deprecated. Use ./scripts/ship.sh instead.
# Usage: ./ship.sh <version> [--deploy]

set -e

echo "=== Wiki Notebook Release Script ==="
echo ""
echo "DEPRECATION NOTICE:"
echo "  This script is deprecated. Use ./scripts/ship.sh instead."
echo ""
echo "Example: ./scripts/ship.sh 0.3.1 --deploy"
echo ""

# Show help
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./ship.sh <version> [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be done without making changes"
    echo "  --deploy     Deploy to production server after building"
    echo "  --skip-tests Skip running test suite"
    echo ""
    echo "Examples:"
    echo "  ./ship.sh 0.2.0              # Full release flow"
    echo "  ./ship.sh 0.2.0 --deploy     # Build, tag, and deploy"
    echo "  ./ship.sh 0.2.0 --dry-run    # Show what would be done"
    exit 0
fi

echo "Running in compatibility mode..."
echo ""
exec ./scripts/ship.sh "$@"
