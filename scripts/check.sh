#!/bin/bash
set -e

echo "🚀 Running local checks (mirroring CI)..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine the python binary to use
if [ -d ".venv" ]; then
  VENV_PYTHON="./.venv/bin/python3"
  echo "ℹ️  Using virtual environment: $VENV_PYTHON"
else
  VENV_PYTHON="python3"
  echo "⚠️  Warning: No .venv found, using system python."
fi

echo "--- 🧼 Formatting (Black & Isort) ---"
# Use --quiet to reduce noise
$VENV_PYTHON -m black --quiet custom_components/custody_schedule tests
$VENV_PYTHON -m isort --quiet custom_components/custody_schedule tests

echo "--- 🔍 Linting (Flake8) ---"
$VENV_PYTHON -m flake8 custom_components/custody_schedule tests --count --select=E9,F63,F7,F82 --show-source --statistics
$VENV_PYTHON -m flake8 custom_components/custody_schedule tests --count --max-complexity=10 --max-line-length=127 --statistics

echo "--- 🧪 Unit Tests (Pytest) ---"
# -c /dev/null: ignore local pytest.ini that might have broken paths
# -p no:cacheprovider: disable .pytest_cache (fixes PermissionError in sandbox)
# --ignore: skip system/temp files
if $VENV_PYTHON -m pytest tests \
    -c /dev/null \
    -p no:cacheprovider \
    --ignore=.DS_Store \
    --ignore=.git \
    --ignore=.gemini \
    --ignore=brain \
    --cov=custom_components/custody_schedule \
    --cov-report=term-missing; then
  echo -e "${GREEN}✅ All checks passed! You can safely push.${NC}"
else
  echo -e "${RED}❌ Tests failed or dependencies missing.${NC}"
  echo "💡 Tip: Make sure to 'pip install -r requirements_test.txt' in your .venv"
  exit 1
fi
