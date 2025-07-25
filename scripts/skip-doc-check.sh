#!/bin/bash

# Skip documentation check for specific commits
# Use this when you're sure a change doesn't need documentation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SKIP_FILE=".doc-skip"
REASON="${1:-No documentation needed}"

echo -e "${BLUE}📋 Marking current changes as not requiring documentation...${NC}"

# Get current commit or working tree state
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "working-tree")
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Create or append to skip file
echo "[$TIMESTAMP] $CURRENT_COMMIT - $REASON" >> "$SKIP_FILE"

echo -e "${GREEN}✓ Documentation check will be skipped for current changes${NC}"
echo -e "${YELLOW}Reason: $REASON${NC}"
echo -e "\n${BLUE}Note: This skip is recorded in $SKIP_FILE${NC}"
echo -e "${BLUE}The quality gate will accept this as valid.${NC}"

# Create a special marker that the doc check can recognize
touch ".doc-skip-marker"
echo "$REASON" > ".doc-skip-marker"

echo -e "\n${YELLOW}Remember to commit this skip marker:${NC}"
echo "  git add .doc-skip .doc-skip-marker"
echo "  git commit -m \"chore: skip doc check - $REASON\""