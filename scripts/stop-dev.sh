#!/bin/bash
# Stop all development server processes

echo "🛑 Stopping all development server processes..."

# Kill React/npm processes
echo "Stopping React dev server..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "chokidar" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

# Kill Flask processes
echo "Stopping Flask server..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true

# Kill any process on port 5000
if command -v lsof >/dev/null 2>&1; then
    echo "Checking port 5000..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
fi

# Kill any node processes that might be hanging
pkill -f "node.*frontend" 2>/dev/null || true

echo "✅ All development server processes stopped"
echo ""
echo "You can now safely restart with 'make dev' or 'python3 dev.py'"