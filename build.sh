#!/bin/bash
# Build script for PostHog Pi

set -e

echo "🚀 Building PostHog Pi..."
echo "========================"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found!"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found!"
    exit 1
fi

# Create backend virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

# Build React app
echo "🔨 Building React application..."
npm run build

cd ..

echo "✅ Build completed successfully!"
echo ""
echo "📋 To run the application:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python3 app.py"
echo ""
echo "🌐 Then visit: http://localhost:5000"