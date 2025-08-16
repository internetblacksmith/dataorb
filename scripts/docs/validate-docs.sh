#!/bin/bash

# Validate documentation against the manifest
# This ensures all features, APIs, and configurations are documented

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📋 Validating documentation against manifest...${NC}"
echo "============================================="

FAILED=0
MANIFEST=".doc-manifest.json"

if [ ! -f "$MANIFEST" ]; then
    echo -e "${RED}✗ Documentation manifest not found!${NC}"
    exit 1
fi

# Function to check if content exists in any doc file
check_documented() {
    local item=$1
    local type=$2
    local found=0
    
    # Search in all markdown files
    if grep -qi "$item" *.md docs/*.md 2>/dev/null; then
        found=1
    fi
    
    if [ $found -eq 1 ]; then
        echo -e "${GREEN}✓ Documented: $item${NC}"
        return 0
    else
        echo -e "${RED}✗ Undocumented $type: $item${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Extract and validate API endpoints
echo -e "\n${YELLOW}Validating API Endpoints:${NC}"
API_ENDPOINTS=$(jq -r '.api_endpoints[]' "$MANIFEST")
while IFS= read -r endpoint; do
    check_documented "$endpoint" "API"
done <<< "$API_ENDPOINTS"

# Validate configuration keys
echo -e "\n${YELLOW}Validating Configuration Keys:${NC}"
CONFIG_KEYS=$(jq -r '.configuration_keys[]' "$MANIFEST")
while IFS= read -r key; do
    check_documented "$key" "Config"
done <<< "$CONFIG_KEYS"

# Validate scripts
echo -e "\n${YELLOW}Validating Scripts Documentation:${NC}"
SCRIPTS=$(jq -r '.scripts[]' "$MANIFEST")
while IFS= read -r script; do
    if [ -f "scripts/$script" ] || [ -f "$script" ]; then
        check_documented "$script" "Script"
    fi
done <<< "$SCRIPTS"

# Validate features
echo -e "\n${YELLOW}Validating Features:${NC}"
FEATURES=$(jq -r '.features[]' "$MANIFEST")
while IFS= read -r feature; do
    # Convert feature names to searchable terms
    search_term=$(echo "$feature" | sed 's/-/ /g')
    check_documented "$search_term" "Feature"
done <<< "$FEATURES"

# Validate documentation files contain required sections
echo -e "\n${YELLOW}Validating Documentation Content:${NC}"
for doc_file in $(jq -r '.documentation_files | keys[]' "$MANIFEST"); do
    if [ -f "$doc_file" ]; then
        echo -e "\n${BLUE}Checking $doc_file:${NC}"
        
        # Get required content for this file
        REQUIRED=$(jq -r ".documentation_files.\"$doc_file\".must_contain[]" "$MANIFEST" 2>/dev/null)
        
        while IFS= read -r required_content; do
            search_pattern=$(echo "$required_content" | sed 's/-/ /g')
            if grep -qi "$search_pattern" "$doc_file"; then
                echo -e "  ${GREEN}✓ Contains: $required_content${NC}"
            else
                echo -e "  ${RED}✗ Missing: $required_content${NC}"
                FAILED=$((FAILED + 1))
            fi
        done <<< "$REQUIRED"
    else
        echo -e "${RED}✗ Documentation file missing: $doc_file${NC}"
        FAILED=$((FAILED + 1))
    fi
done

# Check for orphaned code
echo -e "\n${YELLOW}Checking for Undocumented Code:${NC}"

# Find API routes in code
ACTUAL_ROUTES=$(grep -h "@app.route" backend/app.py 2>/dev/null | sed 's/.*route("\(.*\)").*/\1/' | sort | uniq)
MANIFEST_ROUTES=$(jq -r '.api_endpoints[]' "$MANIFEST" | sort | uniq)

# Compare actual vs documented
UNDOC_ROUTES=$(comm -23 <(echo "$ACTUAL_ROUTES") <(echo "$MANIFEST_ROUTES") 2>/dev/null)
if [ -n "$UNDOC_ROUTES" ]; then
    echo -e "${RED}✗ Undocumented routes found:${NC}"
    echo "$UNDOC_ROUTES"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ All routes are tracked in manifest${NC}"
fi

# Summary
echo -e "\n============================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Documentation validation passed!${NC}"
    echo -e "${BLUE}All features, APIs, and configurations are documented.${NC}"
    exit 0
else
    echo -e "${RED}❌ Documentation validation failed!${NC}"
    echo -e "${RED}Found $FAILED documentation issues.${NC}"
    echo -e "\n${YELLOW}To fix:${NC}"
    echo "1. Update documentation to include missing items"
    echo "2. Update .doc-manifest.json if items were removed"
    echo "3. Run ./scripts/sync-docs.sh after updates"
    exit 1
fi