#!/bin/bash
set -e

echo "🚀 Running local checks (mirroring CI)..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure we are in the virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
  if [ -d ".venv" ]; then
    echo "ℹ️  Activating virtual environment..."
    source .venv/bin/activate
  else
    echo -e "${RED}❌ Error: No virtual environment found. Please create one with 'python3 -m venv .venv'${NC}"
    exit 1
  fi
fi

echo "--- 🧹 Formatting (Black & Isort) ---"
python3 -m black custom_components/custody_schedule tests
python3 -m isort custom_components/custody_schedule tests

echo "--- 🔍 Linting (Flake8) ---"
python3 -m flake8 custom_components/custody_schedule tests --count --select=E9,F63,F7,F82 --show-source --statistics
python3 -m flake8 custom_components/custody_schedule tests --count --max-complexity=10 --max-line-length=127 --statistics

echo "--- 🧪 Unit Tests (Pytest) ---"
if python3 -m pytest tests --cov=custom_components/custody_schedule --cov-report=term-missing; then
  echo -e "${GREEN}✅ All checks passed! You can safely push.${NC}"
else
  echo -e "${RED}❌ Tests failed. Please fix before pushing.${NC}"
  exit 1
fi
