#!/bin/bash

# Install pre-commit hooks for the project

echo "📦 Installing pre-commit..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python 3 and pip first."
    exit 1
fi

# Install pre-commit
pip3 install --user pre-commit

# Install the git hooks
pre-commit install

echo "✅ Pre-commit hooks installed successfully!"
echo "The quality checks will now run automatically before each commit."
echo ""
echo "To run the checks manually, use:"
echo "  pre-commit run --all-files"