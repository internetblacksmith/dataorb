#!/bin/bash

# Intelligent documentation change detection
# This script analyzes code changes to determine what documentation needs updating

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🔍 Analyzing code changes for documentation impact...${NC}"
echo "=================================================="

NEEDS_DOC_UPDATE=0
DOC_SUGGESTIONS=()
SKIP_REASONS=()

# Load ignore patterns if available
IGNORE_CONFIG=".doc-ignore.json"
if [ -f "$IGNORE_CONFIG" ]; then
    echo -e "${PURPLE}📋 Using .doc-ignore.json for filtering${NC}"
fi

# Function to add documentation suggestion
add_suggestion() {
    local file=$1
    local reason=$2
    DOC_SUGGESTIONS+=("$file: $reason")
    NEEDS_DOC_UPDATE=1
}

# Function to check if change should be ignored
should_ignore_change() {
    local change_type=$1
    local file_or_msg=$2
    
    if [ ! -f "$IGNORE_CONFIG" ]; then
        return 1
    fi
    
    # Check ignore patterns
    case "$change_type" in
        "commit")
            # Check if commit message matches ignore patterns
            for pattern in $(jq -r '.ignore_patterns.commits[]' "$IGNORE_CONFIG" 2>/dev/null); do
                if echo "$file_or_msg" | grep -qE "$pattern"; then
                    SKIP_REASONS+=("Commit matches ignore pattern: $pattern")
                    return 0
                fi
            done
            ;;
        "file")
            # Check if file matches ignore patterns
            for pattern in $(jq -r '.ignore_patterns.files[]' "$IGNORE_CONFIG" 2>/dev/null); do
                if [[ "$file_or_msg" == $pattern ]]; then
                    SKIP_REASONS+=("File matches ignore pattern: $pattern")
                    return 0
                fi
            done
            ;;
    esac
    
    return 1
}

# Get the last commit where docs were updated
LAST_DOC_COMMIT=$(git log -1 --format=%H -- "*.md" 2>/dev/null || echo "HEAD")

# Check commit messages first to see if we can skip
echo -e "\n${BLUE}Analyzing recent commits...${NC}"
RECENT_COMMITS=$(git log $LAST_DOC_COMMIT..HEAD --oneline 2>/dev/null | head -10 || true)
DOC_WORTHY_COMMITS=0

if [ -n "$RECENT_COMMITS" ]; then
    while IFS= read -r commit; do
        if ! should_ignore_change "commit" "$commit"; then
            if echo "$commit" | grep -iE "(feat|feature|add|new|breaking|api|config)" > /dev/null; then
                DOC_WORTHY_COMMITS=$((DOC_WORTHY_COMMITS + 1))
            fi
        fi
    done <<< "$RECENT_COMMITS"
    
    if [ $DOC_WORTHY_COMMITS -eq 0 ]; then
        echo -e "${GREEN}✓ No commits requiring documentation found${NC}"
        echo -e "${PURPLE}  (Found only: style, test, refactor, chore changes)${NC}"
    else
        echo -e "${YELLOW}⚠️  Found $DOC_WORTHY_COMMITS commits that may need documentation${NC}"
    fi
fi

# Check for changes since last documentation update
echo -e "\n${BLUE}Changes since last documentation update:${NC}"
echo "----------------------------------------"

# 1. Check for new or modified API endpoints
echo -e "\n${YELLOW}API Endpoints:${NC}"
NEW_ENDPOINTS=$(git diff $LAST_DOC_COMMIT HEAD -- backend/app.py 2>/dev/null | grep -E "^\+.*@app\.route" | sed 's/.*route("\(.*\)").*/\1/' || true)
if [ -n "$NEW_ENDPOINTS" ]; then
    echo -e "${RED}✗ New API endpoints detected:${NC}"
    echo "$NEW_ENDPOINTS" | while read -r endpoint; do
        echo "  - $endpoint"
        add_suggestion "README.md/OTA_README.md" "Document new endpoint: $endpoint"
    done
else
    echo -e "${GREEN}✓ No new API endpoints${NC}"
fi

# 2. Check for new configuration options
echo -e "\n${YELLOW}Configuration Changes:${NC}"
CONFIG_CHANGES=$(git diff $LAST_DOC_COMMIT HEAD -- backend/config_manager.py backend/device_config.json backend/.env.example 2>/dev/null | grep -E "^\+.*['\"].*['\"].*:" || true)
if [ -n "$CONFIG_CHANGES" ]; then
    echo -e "${RED}✗ Configuration changes detected${NC}"
    add_suggestion "QUICK_START.md" "Update configuration documentation"
else
    echo -e "${GREEN}✓ No configuration changes${NC}"
fi

# 3. Check for new scripts
echo -e "\n${YELLOW}New Scripts:${NC}"
NEW_SCRIPTS=$(git diff $LAST_DOC_COMMIT HEAD --name-status 2>/dev/null | grep -E "^A.*\.(sh|py)$" | awk '{print $2}' || true)
if [ -n "$NEW_SCRIPTS" ]; then
    echo -e "${RED}✗ New scripts added:${NC}"
    echo "$NEW_SCRIPTS" | while read -r script; do
        echo "  - $script"
        add_suggestion "QUICK_START.md/README.md" "Document new script: $script"
    done
else
    echo -e "${GREEN}✓ No new scripts${NC}"
fi

# 4. Check for new dependencies
echo -e "\n${YELLOW}Dependency Changes:${NC}"
BACKEND_DEPS=$(git diff $LAST_DOC_COMMIT HEAD -- backend/requirements*.txt 2>/dev/null | grep -E "^\+" | grep -v "^\+\+\+" || true)
FRONTEND_DEPS=$(git diff $LAST_DOC_COMMIT HEAD -- frontend/package.json 2>/dev/null | grep -E "^\+.*:.*\"" || true)
if [ -n "$BACKEND_DEPS" ] || [ -n "$FRONTEND_DEPS" ]; then
    echo -e "${RED}✗ Dependency changes detected${NC}"
    add_suggestion "QUICK_START.md" "Update installation requirements"
else
    echo -e "${GREEN}✓ No dependency changes${NC}"
fi

# 5. Check for new features (by analyzing function additions)
echo -e "\n${YELLOW}New Features:${NC}"
NEW_FUNCTIONS=$(git diff $LAST_DOC_COMMIT HEAD -- "*.py" "*.ts" "*.tsx" 2>/dev/null | grep -E "^\+(def |function |const.*=.*=>|class )" | head -10 || true)
if [ -n "$NEW_FUNCTIONS" ]; then
    echo -e "${RED}✗ New functions/features detected${NC}"
    add_suggestion "README.md/PROJECT_CONTEXT.md" "Document new features"
else
    echo -e "${GREEN}✓ No major feature additions${NC}"
fi

# 6. Check for changes in quality tools
echo -e "\n${YELLOW}Quality Tool Changes:${NC}"
QUALITY_CHANGES=$(git diff $LAST_DOC_COMMIT HEAD -- .pre-commit-config.yaml quality-check.sh backend/pytest.ini backend/pyproject.toml 2>/dev/null || true)
if [ -n "$QUALITY_CHANGES" ]; then
    echo -e "${RED}✗ Quality tool configuration changed${NC}"
    add_suggestion "CLAUDE.md" "Update quality gate documentation"
else
    echo -e "${GREEN}✓ No quality tool changes${NC}"
fi

# 7. Check commit messages for keywords
echo -e "\n${YELLOW}Analyzing commit messages:${NC}"
FEATURE_COMMITS=$(git log $LAST_DOC_COMMIT..HEAD --oneline 2>/dev/null | grep -iE "(add|feature|implement|create|new)" | head -5 || true)
FIX_COMMITS=$(git log $LAST_DOC_COMMIT..HEAD --oneline 2>/dev/null | grep -iE "(fix|bug|patch|resolve)" | head -5 || true)
if [ -n "$FEATURE_COMMITS" ]; then
    echo -e "${YELLOW}⚠️  Feature commits detected - may need documentation${NC}"
fi
if [ -n "$FIX_COMMITS" ]; then
    echo -e "${BLUE}ℹ️  Bug fix commits - check if known issues need updating${NC}"
fi

# 8. Check for TODOs that mention documentation
echo -e "\n${YELLOW}Documentation TODOs:${NC}"
DOC_TODOS=$(grep -r "TODO.*doc" --include="*.py" --include="*.ts" --include="*.tsx" backend/ frontend/src/ 2>/dev/null | head -5 || true)
if [ -n "$DOC_TODOS" ]; then
    echo -e "${YELLOW}⚠️  Found TODOs mentioning documentation:${NC}"
    echo "$DOC_TODOS" | head -3
fi

# Summary and suggestions
echo -e "\n${BLUE}=====================================${NC}"
echo -e "${BLUE}Documentation Update Summary${NC}"
echo -e "${BLUE}=====================================${NC}"

# Show skipped items if any
if [ ${#SKIP_REASONS[@]} -gt 0 ]; then
    echo -e "\n${PURPLE}📋 Changes that don't need documentation:${NC}"
    for reason in "${SKIP_REASONS[@]}"; do
        echo -e "  ${PURPLE}→${NC} $reason"
    done | sort | uniq
fi

# Determine if documentation is really needed
if [ $NEEDS_DOC_UPDATE -eq 1 ]; then
    echo -e "\n${RED}📚 Documentation updates needed:${NC}"
    for suggestion in "${DOC_SUGGESTIONS[@]}"; do
        echo -e "  ${YELLOW}→${NC} $suggestion"
    done
    
    echo -e "\n${YELLOW}Recommended actions:${NC}"
    echo "1. Review the changes listed above"
    echo "2. Update the relevant documentation files"
    echo "3. Run ./scripts/sync-docs.sh to update Docsify"
    echo "4. Run ./quality-check.sh to verify"
    
    exit 1
elif [ $DOC_WORTHY_COMMITS -eq 0 ] && [ ${#SKIP_REASONS[@]} -gt 0 ]; then
    echo -e "\n${GREEN}✅ No documentation updates required!${NC}"
    echo -e "${BLUE}Changes detected were:${NC}"
    echo -e "  • Code refactoring or style improvements"
    echo -e "  • Test additions or modifications"
    echo -e "  • Internal implementation changes"
    echo -e "  • Performance optimizations"
    echo -e "\n${PURPLE}These changes don't affect user-facing features or APIs.${NC}"
    exit 0
else
    echo -e "\n${GREEN}✅ Documentation appears to be up to date!${NC}"
    echo -e "${BLUE}No significant code changes detected since last doc update.${NC}"
    exit 0
fi