#!/bin/bash

# Run backend tests in virtual environment

set -e

echo "🧪 Running backend tests..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Ensure dependencies are installed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Run quality checks
echo ""
echo "🔍 Running Black formatting check..."
black --check app.py config_manager.py ota_manager.py

echo ""
echo "🔍 Running Flake8 linting..."
flake8 app.py config_manager.py ota_manager.py

echo ""
echo "🔍 Running MyPy type checking..."
mypy app.py config_manager.py ota_manager.py

echo ""
echo "🔍 Running pytest..."
pytest tests/ -v

echo ""
echo "✅ All backend tests passed!"

# Deactivate virtual environment
deactivate