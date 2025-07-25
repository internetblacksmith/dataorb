#!/bin/bash

# Documentation Quality Check Script for PostHog Pi
# This script ensures documentation is up-to-date with code changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "📚 Checking Documentation Quality..."
echo "===================================="

FAILED=0
WARNINGS=0

# Function to check if a file exists
check_file_exists() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $description exists${NC}"
        return 0
    else
        echo -e "${RED}✗ $description missing${NC}"
        FAILED=1
        return 1
    fi
}

# Function to check if documentation mentions specific features
check_doc_contains() {
    local file=$1
    local pattern=$2
    local description=$3
    
    if grep -qi "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓ $file documents: $description${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $file missing: $description${NC}"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

# Check required documentation files
echo -e "\n${BLUE}Required Documentation Files${NC}"
echo "----------------------------"
check_file_exists "README.md" "README.md"
check_file_exists "CLAUDE.md" "CLAUDE.md"
check_file_exists "PROJECT_CONTEXT.md" "PROJECT_CONTEXT.md"
check_file_exists "QUICK_START.md" "QUICK_START.md"
check_file_exists "OTA_README.md" "OTA_README.md"

# Check API documentation
echo -e "\n${BLUE}API Documentation${NC}"
echo "-----------------"
# Get all API routes from Flask app
API_ROUTES=$(grep -E "@app.route\(" backend/app.py | sed 's/.*route("\(.*\)").*/\1/' | sort | uniq)
DOCUMENTED_ROUTES=$(grep -E "/(api|config)" README.md QUICK_START.md OTA_README.md 2>/dev/null | grep -oE '/[a-zA-Z0-9/_-]+' | sort | uniq)

echo "Found $(echo "$API_ROUTES" | wc -l) API routes in code"

# Check if key APIs are documented
check_doc_contains "README.md" "/api/health" "Health check endpoint"
check_doc_contains "README.md" "/api/stats" "Stats endpoint"
check_doc_contains "OTA_README.md" "/api/admin/ota" "OTA endpoints"

# Check configuration documentation
echo -e "\n${BLUE}Configuration Documentation${NC}"
echo "---------------------------"
check_doc_contains "QUICK_START.md" "POSTHOG_API_KEY" "PostHog API key setup"
check_doc_contains "QUICK_START.md" ".env" "Environment configuration"
check_doc_contains "README.md" "device_config.json" "Device configuration"

# Check feature documentation
echo -e "\n${BLUE}Feature Documentation${NC}"
echo "----------------------"
# Check if major features are documented
FEATURES=(
    "quality.*check:Quality gate system"
    "pytest:Testing framework"
    "black:Code formatting"
    "prettier:Frontend formatting"
    "OTA.*update:OTA update system"
    "metrics.*config:Metrics configuration"
    "wifi.*setup:WiFi setup"
    "hyperpixel:Display setup"
)

for feature in "${FEATURES[@]}"; do
    IFS=':' read -r pattern description <<< "$feature"
    if grep -qiE "$pattern" README.md QUICK_START.md PROJECT_CONTEXT.md CLAUDE.md 2>/dev/null; then
        echo -e "${GREEN}✓ Documented: $description${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing documentation: $description${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check installation documentation
echo -e "\n${BLUE}Installation Documentation${NC}"
echo "--------------------------"
check_doc_contains "QUICK_START.md" "install-pi.sh" "One-command installer"
check_doc_contains "QUICK_START.md" "npm install" "Frontend setup"
check_doc_contains "QUICK_START.md" "pip install" "Backend setup"

# Check if docs reference current scripts
echo -e "\n${BLUE}Script Documentation${NC}"
echo "--------------------"
SCRIPTS=$(find scripts -name "*.sh" -o -name "*.py" | grep -v __pycache__ | sort)
IMPORTANT_SCRIPTS=(
    "install-pi.sh"
    "quality-check.sh"
    "install-pre-commit.sh"
    "boot-update.py"
    "network-manager.py"
)

for script in "${IMPORTANT_SCRIPTS[@]}"; do
    if grep -q "$script" README.md QUICK_START.md OTA_README.md CLAUDE.md 2>/dev/null; then
        echo -e "${GREEN}✓ Documented: $script${NC}"
    else
        echo -e "${YELLOW}⚠️  Undocumented script: $script${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check for outdated information
echo -e "\n${BLUE}Checking for Outdated Information${NC}"
echo "----------------------------------"
# Check if docs mention old/removed features
OLD_PATTERNS=(
    "gulp:Gulp build system (removed)"
    "webpack.*config:Direct webpack config (using react-scripts)"
)

for pattern_desc in "${OLD_PATTERNS[@]}"; do
    IFS=':' read -r pattern description <<< "$pattern_desc"
    if grep -qiE "$pattern" README.md QUICK_START.md PROJECT_CONTEXT.md 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Outdated reference: $description${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check documentation freshness with intelligent detection
echo -e "\n${BLUE}Documentation Freshness${NC}"
echo "-----------------------"

# Check for skip marker first
if [ -f ".doc-skip-marker" ]; then
    SKIP_REASON=$(cat .doc-skip-marker 2>/dev/null || echo "Unknown reason")
    echo -e "${BLUE}ℹ️  Documentation check skipped${NC}"
    echo -e "${BLUE}   Reason: $SKIP_REASON${NC}"
    echo -e "${GREEN}✓ Changes marked as not requiring documentation${NC}"
elif [ -x "./scripts/detect-doc-changes.sh" ]; then
    echo "Running intelligent change detection..."
    if ./scripts/detect-doc-changes.sh > /tmp/doc-changes.log 2>&1; then
        echo -e "${GREEN}✓ Documentation is up to date with code${NC}"
    else
        # Check if it's just non-doc changes
        if grep -q "No documentation updates required!" /tmp/doc-changes.log; then
            echo -e "${GREEN}✓ No documentation updates required${NC}"
            grep -E "(Code refactoring|Test additions|Internal implementation|Performance)" /tmp/doc-changes.log || true
        else
            echo -e "${YELLOW}⚠️  Documentation may need updates:${NC}"
            grep -E "(→|New|detected)" /tmp/doc-changes.log | head -10 || true
            WARNINGS=$((WARNINGS + 5))  # Higher weight for outdated docs
        fi
    fi
else
    # Fallback to simple timestamp check
    LAST_CODE_CHANGE=$(git log -1 --format=%at -- backend frontend scripts 2>/dev/null || date +%s)
    LAST_DOC_CHANGE=$(git log -1 --format=%at -- "*.md" 2>/dev/null || date +%s)
    
    if [ "$LAST_CODE_CHANGE" -gt "$LAST_DOC_CHANGE" ]; then
        echo -e "${YELLOW}⚠️  Code changed after last documentation update${NC}"
        echo "   Run ./scripts/detect-doc-changes.sh for details"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓ Documentation is up to date with code${NC}"
    fi
fi

# Check Docsify setup
echo -e "\n${BLUE}Docsify Documentation${NC}"
echo "---------------------"

# Check if docs folder exists
if [ -d "docs" ]; then
    echo -e "${GREEN}✓ docs/ folder exists${NC}"
    
    # Check for Docsify files
    DOCSIFY_FILES=("index.html" "_sidebar.md" "_navbar.md" "_coverpage.md" ".nojekyll")
    for file in "${DOCSIFY_FILES[@]}"; do
        if [ -f "docs/$file" ]; then
            echo -e "${GREEN}✓ docs/$file exists${NC}"
        else
            echo -e "${RED}✗ docs/$file missing${NC}"
            FAILED=1
        fi
    done
    
    # Check if docs are synced
    echo -e "\n${BLUE}Checking documentation sync...${NC}"
    NEEDS_SYNC=0
    
    for file in README.md QUICK_START.md PROJECT_CONTEXT.md OTA_README.md CLAUDE.md DOCUMENTATION_CHECKLIST.md; do
        if [ -f "$file" ] && [ -f "docs/$file" ]; then
            if ! cmp -s "$file" "docs/$file"; then
                echo -e "${YELLOW}⚠️  $file is out of sync with docs/$file${NC}"
                NEEDS_SYNC=1
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    done
    
    if [ $NEEDS_SYNC -eq 1 ]; then
        echo -e "${YELLOW}⚠️  Run ./scripts/sync-docs.sh to sync documentation${NC}"
    else
        echo -e "${GREEN}✓ Docsify docs are in sync${NC}"
    fi
else
    echo -e "${RED}✗ docs/ folder missing - run ./scripts/sync-docs.sh${NC}"
    FAILED=1
fi

# Summary
echo -e "\n===================================="
if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Documentation is complete and up to date!${NC}"
    exit 0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Documentation has $WARNINGS warnings${NC}"
    echo -e "${YELLOW}Please review and update documentation${NC}"
    exit 0  # Warnings don't fail the check, but should be addressed
else
    echo -e "${RED}❌ Documentation check failed!${NC}"
    echo -e "${RED}Missing required documentation files${NC}"
    exit 1
fi