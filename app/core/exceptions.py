"""
Custom exceptions for AI-Powered SEO YouTube Assistant.

Cursor Rules:
- Create specific exception classes for different error types
- Include detailed error messages and context
- Support structured error reporting
- Follow consistent naming conventions
"""

from typing import Dict, Any, Optional


class TubeGPTException(Exception):
    """Base exception for TubeGPT application."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class ConfigurationError(TubeGPTException):
    """Configuration related errors."""
    pass


class YouTubeAPIException(TubeGPTException):
    """YouTube API related exceptions."""
    pass


class YouTubeAuthenticationError(YouTubeAPIException):
    """YouTube authentication failures."""
    pass


class YouTubeQuotaExceededError(YouTubeAPIException):
    """YouTube API quota exceeded."""
    pass


class YouTubeVideoNotFoundError(YouTubeAPIException):
    """YouTube video not found."""
    pass


class YouTubeChannelNotFoundError(YouTubeAPIException):
    """YouTube channel not found."""
    pass


class AIServiceException(TubeGPTException):
    """AI service related exceptions."""
    pass


class GeminiAPIException(AIServiceException):
    """Gemini AI API related exceptions."""
    pass


class GeminiRateLimitError(GeminiAPIException):
    """Gemini API rate limit exceeded."""
    pass


class GeminiModelError(GeminiAPIException):
    """Gemini model processing errors."""
    pass


class StorageException(TubeGPTException):
    """Storage related exceptions."""
    pass


class CacheException(TubeGPTException):
    """Cache related exceptions."""
    pass


class ValidationError(TubeGPTException):
    """Input validation errors."""
    pass


class RateLimitError(TubeGPTException):
    """Rate limiting errors."""
    pass


class AuthenticationError(TubeGPTException):
    """Authentication errors."""
    pass


class AuthorizationError(TubeGPTException):
    """Authorization errors."""
    pass


class ServiceUnavailableError(TubeGPTException):
    """Service unavailable errors."""
    pass


class DataProcessingError(TubeGPTException):
    """Data processing errors."""
    pass


class NetworkError(TubeGPTException):
    """Network communication errors."""
    pass


class TimeoutError(TubeGPTException):
    """Operation timeout errors."""
    pass


# HTTP Status Code Mapping
EXCEPTION_STATUS_MAP = {
    ValidationError: 400,
    AuthenticationError: 401,
    AuthorizationError: 403,
    YouTubeVideoNotFoundError: 404,
    YouTubeChannelNotFoundError: 404,
    RateLimitError: 429,
    YouTubeQuotaExceededError: 429,
    GeminiRateLimitError: 429,
    ServiceUnavailableError: 503,
    TimeoutError: 504,
    # Default to 500 for all other exceptions
}


def get_http_status_code(exception: Exception) -> int:
    """Get HTTP status code for exception."""
    return EXCEPTION_STATUS_MAP.get(type(exception), 500) 