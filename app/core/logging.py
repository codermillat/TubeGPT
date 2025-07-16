"""
Structured logging configuration for AI-Powered SEO YouTube Assistant.

Cursor Rules:
- Use structured logging with context binding
- Configure different log levels for different environments
- Include request tracking and performance metrics
- Support JSON formatting for production
"""

import logging
import sys
from typing import Dict, Any, Optional

import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.DEBUG:
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for HTTP requests with correlation IDs."""
    
    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        path: str,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> FilteringBoundLogger:
        """Log HTTP request with context."""
        return self.logger.bind(
            event="request",
            method=method,
            path=path,
            correlation_id=correlation_id,
            user_id=user_id,
            **kwargs
        )
    
    def log_response(
        self,
        status_code: int,
        duration_ms: float,
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> FilteringBoundLogger:
        """Log HTTP response with context."""
        return self.logger.bind(
            event="response",
            status_code=status_code,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            **kwargs
        )


class ServiceLogger:
    """Logger for service operations."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_logger(service_name)
    
    def bind_operation(self, operation: str, **context) -> FilteringBoundLogger:
        """Bind operation context to logger."""
        return self.logger.bind(
            service=self.service_name,
            operation=operation,
            **context
        )
    
    def log_operation_start(self, operation: str, **context) -> FilteringBoundLogger:
        """Log operation start."""
        bound_logger = self.bind_operation(operation, **context)
        bound_logger.info("Operation started")
        return bound_logger
    
    def log_operation_success(
        self,
        operation: str,
        duration_ms: float,
        result_summary: Optional[Dict[str, Any]] = None,
        **context
    ) -> None:
        """Log operation success."""
        self.bind_operation(operation, **context).info(
            "Operation completed successfully",
            duration_ms=duration_ms,
            result=result_summary
        )
    
    def log_operation_error(
        self,
        operation: str,
        error: Exception,
        duration_ms: float,
        **context
    ) -> None:
        """Log operation error."""
        self.bind_operation(operation, **context).error(
            "Operation failed",
            error=str(error),
            error_type=type(error).__name__,
            duration_ms=duration_ms
        )


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger
    
    def log_cache_hit(self, key: str, cache_type: str = "memory") -> None:
        """Log cache hit."""
        self.logger.info(
            "Cache hit",
            event="cache_hit",
            cache_key=key,
            cache_type=cache_type
        )
    
    def log_cache_miss(self, key: str, cache_type: str = "memory") -> None:
        """Log cache miss."""
        self.logger.info(
            "Cache miss",
            event="cache_miss",
            cache_key=key,
            cache_type=cache_type
        )
    
    def log_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        status_code: int,
        **context
    ) -> None:
        """Log external API call."""
        self.logger.info(
            "External API call",
            event="api_call",
            service=service,
            endpoint=endpoint,
            duration_ms=duration_ms,
            status_code=status_code,
            **context
        )
    
    def log_database_query(
        self,
        query_type: str,
        duration_ms: float,
        rows_affected: Optional[int] = None,
        **context
    ) -> None:
        """Log database query."""
        self.logger.info(
            "Database query",
            event="database_query",
            query_type=query_type,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **context
        )


class SecurityLogger:
    """Logger for security events."""
    
    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger
    
    def log_authentication_attempt(
        self,
        user_id: Optional[str],
        success: bool,
        ip_address: str,
        user_agent: str,
        **context
    ) -> None:
        """Log authentication attempt."""
        self.logger.info(
            "Authentication attempt",
            event="auth_attempt",
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            **context
        )
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        limit: int,
        **context
    ) -> None:
        """Log rate limit exceeded."""
        self.logger.warning(
            "Rate limit exceeded",
            event="rate_limit_exceeded",
            ip_address=ip_address,
            endpoint=endpoint,
            limit=limit,
            **context
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        ip_address: str,
        details: Dict[str, Any],
        **context
    ) -> None:
        """Log security violation."""
        self.logger.error(
            "Security violation",
            event="security_violation",
            violation_type=violation_type,
            ip_address=ip_address,
            details=details,
            **context
        )


# Initialize logging when module is imported
configure_logging()

# Pre-configured logger instances
app_logger = get_logger("app")
request_logger = RequestLogger(get_logger("request"))
performance_logger = PerformanceLogger(get_logger("performance"))
security_logger = SecurityLogger(get_logger("security")) 