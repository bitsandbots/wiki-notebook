#!/bin/bash
# Run Playwright UI tests
# Usage: ./scripts/run_ui_tests.sh [browser]
# browser: chromium (default), firefox, webkit

BROWSER="${1:-chromium}"

echo "Installing Playwright browsers..."
playwright install "$BROWSER" --with-deps 2>/dev/null || pip install pytest-playwright && playwright install "$BROWSER" --with-deps

echo ""
echo "Running UI tests with $BROWSER..."
pytest tests/ui/ --browser "$BROWSER" -v
