#!/usr/bin/env python3
"""
Simple startup script for TubeGPT server with playground
"""

import uvicorn
from pathlib import Path
import os
import sys

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main app
from app.api.v1.main import app

if __name__ == "__main__":
    print("🎯 Starting TubeGPT Server...")
    print("📱 Local Playground: http://127.0.0.1:8000/playground")
    print("🔧 API Documentation: http://127.0.0.1:8000/docs")
    print("ℹ️  Press Ctrl+C to stop")
    print()
    
    # Ensure directories exist
    Path("data/storage/strategies").mkdir(parents=True, exist_ok=True)
    Path("data/storage/cache").mkdir(parents=True, exist_ok=True)
    
    # Start server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
