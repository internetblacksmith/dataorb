#!/bin/bash

# Preview Docsify documentation locally

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📚 Starting Docsify documentation preview...${NC}"

# Check if docs folder exists
if [ ! -d "docs" ]; then
    echo -e "${YELLOW}⚠️  docs/ folder not found. Running sync...${NC}"
    ./scripts/sync-docs.sh
fi

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo -e "${YELLOW}⚠️  npx not found. Installing docsify-cli globally...${NC}"
    npm install -g docsify-cli
    docsify serve docs
else
    echo -e "${GREEN}✓ Starting Docsify server...${NC}"
    echo -e "${BLUE}📄 Documentation will be available at: http://localhost:3000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    npx docsify serve docs
fi