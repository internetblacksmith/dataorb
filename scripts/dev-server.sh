#!/bin/bash
# Development server script with proper cleanup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Store PIDs
REACT_PID=""
FLASK_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping development servers...${NC}"
    
    # Kill React process and its children
    if [ ! -z "$REACT_PID" ]; then
        echo "Stopping React dev server (PID: $REACT_PID)..."
        # Kill the entire process group
        kill -TERM -$REACT_PID 2>/dev/null || true
        wait $REACT_PID 2>/dev/null || true
    fi
    
    # Kill Flask process and its children
    if [ ! -z "$FLASK_PID" ]; then
        echo "Stopping Flask server (PID: $FLASK_PID)..."
        kill -TERM $FLASK_PID 2>/dev/null || true
        wait $FLASK_PID 2>/dev/null || true
    fi
    
    # Kill any remaining npm/node processes
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "chokidar.*src" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All servers stopped${NC}"
    exit 0
}

# Set up trap for cleanup on exit
trap cleanup EXIT INT TERM

echo -e "${BLUE}🚀 Starting Pi Analytics Dashboard Development Server${NC}"
echo "======================================================"

# Check if directories exist
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found!${NC}"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Backend directory not found!${NC}"
    exit 1
fi

# Start React development build with file watching
echo -e "${BLUE}🔨 Starting React file watcher...${NC}"
cd frontend
npm run dev &
REACT_PID=$!
cd ..
echo -e "${GREEN}✅ React file watcher started (PID: $REACT_PID)${NC}"

# Give React a moment to start
sleep 3

# Start Flask development server
echo -e "${BLUE}🌶️  Starting Flask development server...${NC}"
cd backend

# Check if venv exists
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found, using system Python${NC}"
    PYTHON_CMD="python3"
fi

FLASK_DEBUG=1 $PYTHON_CMD app.py &
FLASK_PID=$!
cd ..
echo -e "${GREEN}✅ Flask development server started (PID: $FLASK_PID)${NC}"

echo ""
echo -e "${GREEN}🎉 Development servers are running!${NC}"
echo "📱 Frontend: React file watcher active"
echo "🔧 Backend: Flask with auto-reload at http://localhost:5000"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop all servers${NC}"

# Wait for both processes
wait $REACT_PID $FLASK_PID