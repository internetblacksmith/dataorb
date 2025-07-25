#!/bin/bash

# Quality Gate Script for PostHog Pi
# This script runs all quality checks for the project

set -e  # Exit on any error

echo "🔍 Running PostHog Pi Quality Gate..."
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    
    echo -e "\n🔍 Running: $name"
    if eval "$command"; then
        echo -e "${GREEN}✓ $name passed${NC}"
    else
        echo -e "${RED}✗ $name failed${NC}"
        FAILED=1
    fi
}

# Backend checks
echo -e "\n${YELLOW}Backend Quality Checks${NC}"
echo "------------------------"

# Save current directory
ORIGINAL_DIR=$(pwd)

# Run backend tests in a subshell to properly manage venv
(
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Ensure dependencies are installed
    echo "📦 Ensuring dependencies are up to date..."
    # Check if pip is from venv
    if [[ "$(which pip)" == *"/venv/"* ]]; then
        pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt
        pip install -q -r requirements-dev.txt 2>/dev/null || pip install -r requirements-dev.txt
    else
        echo -e "${RED}Error: Virtual environment not properly activated${NC}"
        exit 1
    fi
    
    # Run checks with venv active
    run_check "Black formatting" "black --check app.py config_manager.py ota_manager.py"
    run_check "Flake8 linting" "flake8 app.py config_manager.py ota_manager.py"
    run_check "MyPy type checking" "mypy app.py config_manager.py ota_manager.py"
    run_check "Python tests" "pytest tests/ -v"
)

# Return to original directory
cd "$ORIGINAL_DIR"

# Frontend checks
echo -e "\n${YELLOW}Frontend Quality Checks${NC}"
echo "-------------------------"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found. Installing...${NC}"
    npm install
fi

run_check "ESLint" "npm run lint"
run_check "Prettier formatting" "npm run format:check"
run_check "TypeScript compilation" "npx tsc --noEmit"
run_check "React tests" "npm run test -- --watchAll=false --passWithNoTests"

cd ..

# Documentation checks
echo -e "\n${YELLOW}Documentation Checks${NC}"
echo "----------------------"

# Sync documentation to docs folder for Docsify
if [ -x "./scripts/sync-docs.sh" ]; then
    echo "📚 Syncing documentation for Docsify..."
    ./scripts/sync-docs.sh > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Documentation synced to docs/${NC}"
    else
        echo -e "${RED}✗ Failed to sync documentation${NC}"
        FAILED=1
    fi
fi

# Run comprehensive documentation quality check
if [ -x "./scripts/check-docs.sh" ]; then
    ./scripts/check-docs.sh
    DOC_CHECK_STATUS=$?
    if [ $DOC_CHECK_STATUS -ne 0 ]; then
        FAILED=1
    fi
else
    run_check "CLAUDE.md exists" "[ -f CLAUDE.md ]"
    run_check "README.md exists" "[ -f README.md ]"
    run_check "PROJECT_CONTEXT.md exists" "[ -f PROJECT_CONTEXT.md ]"
    echo -e "${YELLOW}⚠️  Documentation quality script not found. Run ./scripts/check-docs.sh for detailed checks${NC}"
fi

# Check for TODOs in code
echo -e "\n${YELLOW}Code TODOs${NC}"
echo "------------"
TODO_COUNT=$(grep -r "TODO" --include="*.py" --include="*.ts" --include="*.tsx" backend/ frontend/src/ 2>/dev/null | wc -l || echo "0")
if [ "$TODO_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $TODO_COUNT TODOs in code${NC}"
    grep -r "TODO" --include="*.py" --include="*.ts" --include="*.tsx" backend/ frontend/src/ 2>/dev/null | head -5 || true
    if [ "$TODO_COUNT" -gt 5 ]; then
        echo "... and $((TODO_COUNT - 5)) more"
    fi
fi

# Final summary
echo -e "\n====================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some quality checks failed!${NC}"
    echo -e "${YELLOW}Please fix the issues above before committing.${NC}"
    exit 1
fi