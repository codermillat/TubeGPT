"""
Dependency injection for AI-Powered SEO YouTube Assistant.

Cursor Rules:
- Use dependency injection for all external dependencies
- Create reusable dependency providers
- Support testing with mock dependencies
- Follow FastAPI dependency injection patterns
"""

import aiohttp
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.core.logging import get_logger
from app.services.ai_service import AIService
from app.services.memory_service import MemoryService
from app.services.cache_service import CacheService
from app.clients.youtube_client import YouTubeClient
from app.clients.gemini_client import GeminiClient

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


# HTTP Session Dependencies
async def get_http_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Provide HTTP session for external API calls."""
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


# Client Dependencies
async def get_gemini_client(
    session: aiohttp.ClientSession = Depends(get_http_session)
) -> GeminiClient:
    """Get Gemini AI client instance."""
    if not settings.GEMINI_API_KEY:
        raise ConfigurationError("GEMINI_API_KEY is not configured")
    
    return GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        session=session
    )


async def get_youtube_client(
    session: aiohttp.ClientSession = Depends(get_http_session)
) -> YouTubeClient:
    """Get YouTube API client instance."""
    return YouTubeClient(
        credentials_file=settings.YOUTUBE_CREDENTIALS_FILE,
        token_file=settings.YOUTUBE_TOKEN_FILE,
        session=session
    )


# Service Dependencies
async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    return CacheService(
        redis_url=settings.REDIS_URL,
        cache_path=settings.CACHE_PATH,
        ttl_seconds=settings.CACHE_TTL,
        max_size=settings.CACHE_MAX_SIZE
    )


async def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    return MemoryService(
        storage_path=settings.STRATEGY_STORAGE_PATH
    )


async def get_ai_service(
    gemini_client: GeminiClient = Depends(get_gemini_client),
    cache_service: CacheService = Depends(get_cache_service)
) -> AIService:
    """Get AI service instance."""
    return AIService(
        gemini_client=gemini_client,
        cache_service=cache_service
    )


# Authentication Dependencies
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Get current authenticated user (optional)."""
    if not credentials:
        return None
    
    try:
        # TODO: Implement JWT token validation
        # For now, return None (no authentication required)
        return None
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise AuthenticationError("Invalid authentication credentials")


async def require_authentication(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Require authentication (when needed)."""
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    try:
        # TODO: Implement JWT token validation
        # For now, raise error since auth is not implemented
        raise AuthenticationError("Authentication not implemented")
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise AuthenticationError("Invalid authentication credentials")


# Request Context Dependencies
async def get_request_id(request: Request) -> str:
    """Get or generate request ID for tracing."""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())
    return request_id


async def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


async def get_user_agent(request: Request) -> str:
    """Get user agent string."""
    return request.headers.get("User-Agent", "Unknown")


# Validation Dependencies
async def validate_video_id(video_id: str) -> str:
    """Validate YouTube video ID format."""
    import re
    
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube video ID format"
        )
    return video_id


async def validate_channel_id(channel_id: str) -> str:
    """Validate YouTube channel ID format."""
    import re
    
    if not re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube channel ID format"
        )
    return channel_id


# Rate Limiting Dependencies
class RateLimitChecker:
    """Rate limit checker for API endpoints."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def check_rate_limit(self, client_ip: str = Depends(get_client_ip)) -> bool:
        """Check if request is within rate limit."""
        import time
        
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        return True


# Create rate limiter instances
standard_rate_limiter = RateLimitChecker(requests_per_minute=60)
strict_rate_limiter = RateLimitChecker(requests_per_minute=30)


# Dependency shortcuts
async def get_standard_rate_limit():
    """Standard rate limit dependency."""
    return Depends(standard_rate_limiter.check_rate_limit)


async def get_strict_rate_limit():
    """Strict rate limit dependency."""
    return Depends(strict_rate_limiter.check_rate_limit)


# Health Check Dependencies
async def health_check_youtube(
    youtube_client: YouTubeClient = Depends(get_youtube_client)
) -> bool:
    """Check YouTube API health."""
    try:
        # Simple health check - just test connection
        await youtube_client.health_check()
        return True
    except Exception:
        return False


async def health_check_gemini(
    gemini_client: GeminiClient = Depends(get_gemini_client)
) -> bool:
    """Check Gemini API health."""
    try:
        # Simple health check - just test connection
        await gemini_client.health_check()
        return True
    except Exception:
        return False


# Context manager for performance tracking
class PerformanceContext:
    """Context manager for tracking operation performance."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.duration = None
    
    async def __aenter__(self):
        import time
        self.start_time = time.time()
        logger.info(f"Starting {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        self.duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
        
        if exc_type:
            logger.error(
                f"{self.operation_name} failed",
                duration_ms=self.duration,
                error=str(exc_val)
            )
        else:
            logger.info(
                f"{self.operation_name} completed",
                duration_ms=self.duration
            )


def get_performance_context(operation_name: str) -> PerformanceContext:
    """Get performance tracking context manager."""
    return PerformanceContext(operation_name) 