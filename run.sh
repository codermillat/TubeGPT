#!/bin/bash

# AI SEO Assistant - Run Script
# This script starts the FastAPI backend and opens the frontend in a browser

set -e  # Exit on any error

echo "🚀 Starting AI SEO Assistant..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip

# Install basic dependencies
pip install fastapi uvicorn pydantic python-multipart

# Install additional dependencies (if requirements.txt exists)
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Create necessary directories
mkdir -p strategy_storage
mkdir -p backend
mkdir -p frontend

# Check if backend files exist
if [ ! -f "backend/api.py" ]; then
    echo "❌ Backend files not found. Please ensure all backend files are in the backend/ directory."
    exit 1
fi

# Check if frontend files exist
if [ ! -f "frontend/index.html" ]; then
    echo "❌ Frontend files not found. Please ensure all frontend files are in the frontend/ directory."
    exit 1
fi

echo "✅ Setup complete!"
echo ""
echo "🖥️  Starting AI SEO Assistant server..."
echo "    Backend: http://127.0.0.1:8000"
echo "    Frontend: http://127.0.0.1:8000"
echo ""
echo "📁 Strategies will be saved to: ./strategy_storage/"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Function to open browser (platform-specific)
open_browser() {
    local url=$1
    echo "🌐 Opening browser to $url..."
    
    # Delay to ensure server is ready
    sleep 3
    
    if command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "$url" &
    elif command -v open &> /dev/null; then
        # macOS
        open "$url" &
    elif command -v start &> /dev/null; then
        # Windows (Git Bash)
        start "$url" &
    else
        echo "ℹ️  Please open your browser and go to: $url"
    fi
}

# Start the server in background and open browser
cd backend
open_browser "http://127.0.0.1:8000" &
python3 -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Shutting down AI SEO Assistant..."
    echo "💾 All strategies have been saved to ./strategy_storage/"
    echo "👋 Thanks for using AI SEO Assistant!"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup INT TERM 