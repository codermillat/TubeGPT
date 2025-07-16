# FIXED: Updated with thread-safe session management and security improvements
"""
FastAPI Chat API for YouTube Analytics with Gemini Integration.
Provides a REST endpoint for analyzing YouTube data using AI.
FIXED: Enhanced with thread-safe session management, rate limiting, and security.
"""

import os
import logging
import uuid
import hashlib
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# FIXED: Import new modules for better architecture
try:
    from gemini_chat import GeminiYouTubeAnalyzer
except ImportError as e:
    logging.error(f"Failed to import GeminiYouTubeAnalyzer: {e}")
    GeminiYouTubeAnalyzer = None

# FIXED: Import new thread-safe session manager
from session_manager import session_manager

# FIXED: Import CSV validator for security
from csv_validator import csv_validator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FIXED: Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Analytics Chat API",
    description="AI-powered analysis of YouTube analytics data using Gemini Pro",
    version="1.0.0"
)

# FIXED: Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# FIXED: Secure CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # FIXED: No more wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # FIXED: Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # FIXED: Specific headers only
)

# Global analyzer instance
analyzer = None

# FIXED: Removed old session management code - now using thread-safe session_manager

def validate_csv_file(file_path: str) -> bool:
    """
    Validate CSV file for security and data integrity.
    FIXED: Uses new CSV validator for comprehensive validation.
    
    Args:
        file_path (str): Path to CSV file
        
    Returns:
        bool: True if file is valid and safe
    """
    try:
        # FIXED: Quick validation for basic checks
        if not csv_validator.quick_validate(file_path):
            return False
        
        # FIXED: Full validation for security
        validation_results = csv_validator.validate_csv_file(file_path)
        
        # Check if validation passed
        if not validation_results.get('valid', False):
            return False
        
        # Check for security issues
        security_validation = validation_results.get('security_validation', {})
        if not security_validation.get('is_secure', True):
            logger.warning(f"Security issues found in CSV file: {file_path}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"CSV validation failed: {e}")
        return False
    
    # Keep only last 10 messages per session to prevent memory bloat
    if len(SESSION_MEMORY[session_id]) > 10:
        SESSION_MEMORY[session_id] = SESSION_MEMORY[session_id][-10:]
    
    logger.info(f"Stored message for session {session_id}. Total messages: {len(SESSION_MEMORY[session_id])}")

def summarize_old_messages(messages: list, max_length: int = 500) -> str:
    """
    Summarize old messages if context gets too long.
    
    Args:
        messages (list): List of SessionMessage objects
        max_length (int): Maximum length for summary
        
    Returns:
        str: Summarized context
    """
    if not messages:
        return ""
    
    # Create a brief summary of older messages
    topics = []
    for msg in messages:
        # Extract key topics from user messages
        user_msg_lower = msg.user_message.lower()
        if any(keyword in user_msg_lower for keyword in ['views', 'view']):
            topics.append('video views')
        if any(keyword in user_msg_lower for keyword in ['ctr', 'click']):
            topics.append('click-through rates')
        if any(keyword in user_msg_lower for keyword in ['duration', 'watch time']):
            topics.append('watch duration')
        if any(keyword in user_msg_lower for keyword in ['country', 'geographic']):
            topics.append('geographic performance')
        if any(keyword in user_msg_lower for keyword in ['compare', 'comparison']):
            topics.append('performance comparisons')
    
    unique_topics = list(set(topics))
    
    if unique_topics:
        summary = f"Previous conversation covered: {', '.join(unique_topics[:5])}"
    else:
        summary = f"Previous conversation included {len(messages)} messages about YouTube analytics"
    
    return summary[:max_length]

def initialize_analyzer() -> Optional[GeminiYouTubeAnalyzer]:
    """
    Initialize the Gemini analyzer with proper error handling.
    
    Returns:
        GeminiYouTubeAnalyzer instance or None if initialization fails
    """
    global analyzer
    
    if analyzer is not None:
        return analyzer
    
    if GeminiYouTubeAnalyzer is None:
        logger.error("GeminiYouTubeAnalyzer not available")
        return None
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return None
        
        analyzer = GeminiYouTubeAnalyzer(api_key=api_key)
        logger.info("Gemini analyzer initialized successfully")
        return analyzer
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini analyzer: {e}")
        return None

# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=1000, description="User's question about YouTube analytics")
    csv_path: str = Field(..., min_length=1, description="Path to YouTube analytics CSV file")
    session_id: Optional[str] = Field(None, description="Session ID for conversation memory")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate and clean the message."""
        v = v.strip()
        if not v:
            raise ValueError('Message cannot be empty or whitespace only')
        return v
    
    @validator('csv_path')
    def validate_csv_path(cls, v):
        """Validate CSV path format."""
        v = v.strip()
        if not v.endswith('.csv'):
            raise ValueError('CSV path must end with .csv extension')
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if v is not None:
            v = v.strip()
            if len(v) > 100:  # Reasonable limit
                raise ValueError('Session ID too long')
        return v

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    reply: str = Field(..., description="AI-generated response to user's question")
    status: str = Field(..., description="Response status: 'success' or 'error'")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    error_details: Optional[str] = Field(None, description="Additional error information if status is 'error'")

def analyze_with_gemini(message: str, csv_path: str, session_context: str = "") -> str:
    """
    Analyze YouTube data using Gemini AI.
    
    Args:
        message (str): User's question
        csv_path (str): Path to CSV file
        session_context (str): Previous conversation context
        
    Returns:
        str: Gemini's analysis response
        
    Raises:
        Exception: If analysis fails
    """
    analyzer_instance = initialize_analyzer()
    
    if analyzer_instance is None:
        raise Exception("Gemini analyzer not available. Please check your API key and configuration.")
    
    try:
        # Add session context to the message if available
        enhanced_message = message
        if session_context:
            enhanced_message = f"{session_context}\n\nCURRENT QUESTION: {message}"
        
        response = analyzer_instance.analyze_youtube_data(enhanced_message, csv_path)
        return response
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        raise Exception(f"Analysis failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "YouTube Analytics Chat API is running",
        "status": "healthy",
        "gemini_available": analyzer is not None or initialize_analyzer() is not None
    }

# FIXED: Updated health check and added session management endpoints
@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    # FIXED: Cleanup old sessions during health check using new session manager
    cleanup_count = session_manager.cleanup_expired_sessions()
    
    gemini_status = "available" if initialize_analyzer() is not None else "unavailable"
    api_key_configured = bool(os.getenv('GEMINI_API_KEY'))
    session_stats = session_manager.get_stats()
    
    return {
        "status": "healthy",
        "gemini_analyzer": gemini_status,
        "api_key_configured": api_key_configured,
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "session_stats": session_stats,
        "cleanup_count": cleanup_count
    }

@app.get("/sessions/stats")
async def get_session_stats():
    """Get session manager statistics."""
    return session_manager.get_stats()

@app.get("/sessions")
async def get_all_sessions():
    """Get information about all active sessions."""
    return session_manager.get_all_sessions()

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session."""
    removed = session_manager.remove_session(session_id)
    if removed:
        return {"message": f"Session {session_id} removed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

@app.delete("/sessions")
async def clear_all_sessions():
    """Clear all sessions (admin endpoint)."""
    count = session_manager.clear_all_sessions()
    return {"message": f"Cleared {count} sessions"}

# FIXED: Updated chat endpoint with rate limiting and new session manager
@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # FIXED: Rate limiting per IP
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """
    Main chat endpoint for YouTube analytics analysis.
    FIXED: Enhanced with rate limiting, secure validation, and thread-safe session management.
    
    Args:
        request (Request): FastAPI request object for rate limiting
        chat_request (ChatRequest): Contains user message and CSV path
        
    Returns:
        ChatResponse: AI analysis response with status
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(f"Received chat request: message='{chat_request.message[:50]}...', csv_path='{chat_request.csv_path}'")
        
        # Generate session ID if not provided
        session_id = chat_request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        
        # FIXED: Comprehensive CSV validation
        if not validate_csv_file(chat_request.csv_path):
            logger.warning(f"CSV validation failed: {chat_request.csv_path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV file validation failed: {chat_request.csv_path}. Please ensure the file is properly formatted and safe."
            )
        
        # FIXED: Get conversation context using new session manager
        session_context = session_manager.get_session_context(session_id, max_messages=3)
        
        # Analyze with Gemini
        try:
            response_text = analyze_with_gemini(chat_request.message, chat_request.csv_path, session_context)
            
            if not response_text or response_text.strip() == "":
                logger.warning("Received empty response from Gemini")
                response_text = "I apologize, but I couldn't generate a meaningful response to your question. Please try rephrasing or asking a different question about your YouTube analytics."
            
            # FIXED: Store the conversation using new session manager
            session_manager.add_message(session_id, chat_request.message, response_text, chat_request.csv_path)
            
            logger.info("Successfully generated response")
            return ChatResponse(
                reply=response_text,
                status="success",
                session_id=session_id
            )
            
        except Exception as analysis_error:
            logger.error(f"Analysis error: {analysis_error}")
            
            # Check for specific error types
            error_message = str(analysis_error).lower()
            
            if "api key" in error_message or "authentication" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Gemini API authentication failed. Please check your API key configuration."
                )
            elif "quota" in error_message or "rate limit" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API rate limit exceeded. Please try again later."
                )
            elif "csv" in error_message or "data" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data processing error: {analysis_error}"
                )
            else:
                # Generic analysis error
                return ChatResponse(
                    reply="I encountered an error while analyzing your data. Please try again or rephrase your question.",
                    status="error",
                    session_id=session_id,
                    error_details=str(analysis_error)
                )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "reply": "An unexpected error occurred. Please try again later.",
        "status": "error",
        "session_id": "error",
        "error_details": "Internal server error"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting YouTube Analytics Chat API...")
    
    # Initialize Gemini analyzer
    if initialize_analyzer():
        logger.info("Gemini analyzer ready")
    else:
        logger.warning("Gemini analyzer initialization failed - API will have limited functionality")
    
    # Initialize session memory
    logger.info("Session memory initialized")
    
    logger.info("API startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down YouTube Analytics Chat API...")
    
    # Clear session memory
    SESSION_MEMORY.clear()
    logger.info("Session memory cleared")

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "chat_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )