"""
Core configuration for AI-Powered SEO YouTube Assistant.

Cursor Rules:
- Use environment variables for all configuration
- Validate all settings with Pydantic
- Group related settings together
- Add descriptive docstrings
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Configuration
    APP_NAME: str = Field(
        default="AI-Powered SEO YouTube Assistant",
        description="Application name"
    )
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Server Configuration
    HOST: str = Field(default="127.0.0.1", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload server")

    # YouTube API Configuration
    YOUTUBE_CREDENTIALS_FILE: str = Field(
        default="config/credentials.json",
        description="Path to YouTube OAuth credentials file"
    )
    YOUTUBE_TOKEN_FILE: str = Field(
        default="data/storage/token.json",
        description="Path to YouTube OAuth token file"
    )
    YOUTUBE_API_BASE_URL: str = Field(
        default="https://www.googleapis.com/youtube/v3",
        description="YouTube API base URL"
    )
    YOUTUBE_API_QUOTA_LIMIT: int = Field(
        default=10000,
        description="YouTube API daily quota limit"
    )

    # Gemini AI Configuration
    GEMINI_API_KEY: str = Field(
        default="",
        description="Gemini AI API key"
    )
    GEMINI_MODEL: str = Field(
        default="gemini-pro",
        description="Gemini AI model to use"
    )
    GEMINI_MAX_TOKENS: int = Field(
        default=2048,
        description="Maximum tokens for Gemini responses"
    )

    # Storage Configuration
    STORAGE_PATH: str = Field(
        default="data/storage",
        description="Base path for data storage"
    )
    STRATEGY_STORAGE_PATH: str = Field(
        default="data/storage/strategies",
        description="Path for strategy storage"
    )
    CACHE_PATH: str = Field(
        default="data/storage/cache",
        description="Path for cache storage"
    )

    # Cache Configuration
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum cache size")
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis URL for caching (optional)"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        description="Rate limit requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )

    # Security
    SECRET_KEY: str = Field(
        description="Secret key for JWT tokens (required)"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:8000"],
        description="CORS allowed origins"
    )

    # Monitoring
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    HEALTH_CHECK_INTERVAL: int = Field(
        default=30,
        description="Health check interval in seconds"
    )

    @validator('STORAGE_PATH', 'STRATEGY_STORAGE_PATH', 'CACHE_PATH')
    def create_directories(cls, v):
        """Create directories if they don't exist."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @validator('GEMINI_API_KEY')
    def validate_gemini_key(cls, v):
        """Validate Gemini API key is provided."""
        if not v and not os.getenv('MOCK_AI', False):
            raise ValueError("GEMINI_API_KEY is required")
        return v

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        """Validate secret key is provided and secure."""
        if not v:
            raise ValueError("SECRET_KEY is required for security")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")
        if v in ["your-secret-key-change-in-production", "secret", "password", "123456"]:
            raise ValueError("SECRET_KEY cannot be a common/default value")
        return v

    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings 