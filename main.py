"""
Main entry point for AI-Powered SEO YouTube Assistant.

This file serves as the main entry point for the application,
initializing the FastAPI app and running it with uvicorn.
"""

import uvicorn
from app.api.v1.main import app
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )