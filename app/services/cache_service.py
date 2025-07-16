"""
Cache Service for YouTube SEO Assistant.

Cursor Rules:
- Implement proper async/await patterns
- Add comprehensive error handling with structured logging
- Support multiple cache levels (memory, file, Redis)
- Fail gracefully when cache is unavailable
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union

from app.core.config import settings
from app.core.exceptions import CacheException
from app.core.logging import ServiceLogger

# Initialize service logger
logger = ServiceLogger("cache_service")


class CacheService:
    """Multi-level cache service with memory, file, and Redis support."""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        cache_path: str = "data/storage/cache",
        ttl_seconds: int = 3600,
        max_size: int = 1000
    ):
        """
        Initialize cache service.
        
        Args:
            redis_url: Optional Redis connection URL
            cache_path: Path for file-based cache
            ttl_seconds: Default TTL for cache entries
            max_size: Maximum number of entries in memory cache
        """
        self.redis_url = redis_url
        self.cache_path = Path(cache_path)
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.logger = logger
        
        # Memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        
        # Redis client (optional)
        self.redis_client = None
        
        # Initialize storage
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Redis if available
        if self.redis_url:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client."""
        try:
            import aioredis
            self.redis_client = aioredis.from_url(self.redis_url)
            self.logger.logger.info("Redis cache initialized")
        except ImportError:
            self.logger.logger.warning("Redis not available, skipping Redis cache")
        except Exception as e:
            self.logger.logger.error(f"Failed to initialize Redis: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with fallback strategy.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "cache_get",
            key=key[:50]  # Truncate key for logging
        )
        
        try:
            bound_logger.info("Starting cache lookup")
            
            # Level 1: Memory cache
            memory_result = await self._get_from_memory(key)
            if memory_result is not None:
                bound_logger.info("Cache hit: memory")
                return memory_result
            
            # Level 2: Redis cache
            if self.redis_client:
                redis_result = await self._get_from_redis(key)
                if redis_result is not None:
                    bound_logger.info("Cache hit: Redis")
                    # Populate memory cache
                    await self._set_in_memory(key, redis_result)
                    return redis_result
            
            # Level 3: File cache
            file_result = await self._get_from_file(key)
            if file_result is not None:
                bound_logger.info("Cache hit: file")
                # Populate higher-level caches
                await self._set_in_memory(key, file_result)
                if self.redis_client:
                    await self._set_in_redis(key, file_result)
                return file_result
            
            bound_logger.info("Cache miss: all levels")
            return None
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "cache_get",
                error=e,
                duration_ms=duration_ms,
                key=key[:50]
            )
            # Fail gracefully - return None if cache fails
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Set value in cache across all levels.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (optional)
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "cache_set",
            key=key[:50],
            value_type=type(value).__name__
        )
        
        try:
            bound_logger.info("Starting cache set")
            
            # Calculate expiration time
            expiration = datetime.now() + (ttl or timedelta(seconds=self.ttl_seconds))
            
            # Set in all cache levels
            success = True
            
            # Memory cache
            await self._set_in_memory(key, value, expiration)
            
            # Redis cache
            if self.redis_client:
                redis_success = await self._set_in_redis(key, value, expiration)
                success = success and redis_success
            
            # File cache
            file_success = await self._set_in_file(key, value, expiration)
            success = success and file_success
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "cache_set",
                duration_ms=duration_ms,
                result_summary={"success": success},
                key=key[:50]
            )
            
            return success
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "cache_set",
                error=e,
                duration_ms=duration_ms,
                key=key[:50]
            )
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from all cache levels.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from memory
            self.memory_cache.pop(key, None)
            self.access_times.pop(key, None)
            
            # Delete from Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    self.logger.logger.warning(f"Failed to delete from Redis: {e}")
            
            # Delete from file
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache levels.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear memory cache
            self.memory_cache.clear()
            self.access_times.clear()
            
            # Clear Redis cache
            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    self.logger.logger.warning(f"Failed to clear Redis: {e}")
            
            # Clear file cache
            for file_path in self.cache_path.glob("*.json"):
                file_path.unlink()
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to clear cache: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for cache service.
        
        Returns:
            Health check results
        """
        try:
            # Test memory cache
            test_key = "health_check_test"
            test_value = {"timestamp": time.time()}
            
            await self.set(test_key, test_value)
            retrieved = await self.get(test_key)
            memory_healthy = retrieved is not None
            
            # Test Redis if available
            redis_healthy = True
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                except Exception:
                    redis_healthy = False
            
            # Test file cache
            file_healthy = self.cache_path.exists() and self.cache_path.is_dir()
            
            # Clean up test data
            await self.delete(test_key)
            
            return {
                "status": "healthy" if memory_healthy and redis_healthy and file_healthy else "degraded",
                "memory_cache": memory_healthy,
                "redis_cache": redis_healthy,
                "file_cache": file_healthy,
                "cache_size": len(self.memory_cache),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self.memory_cache:
            return None
        
        entry = self.memory_cache[key]
        
        # Check expiration
        if datetime.now() > entry["expires_at"]:
            self.memory_cache.pop(key, None)
            self.access_times.pop(key, None)
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        
        return entry["value"]
    
    async def _set_in_memory(
        self,
        key: str,
        value: Any,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Set value in memory cache."""
        try:
            # Evict if at capacity
            if len(self.memory_cache) >= self.max_size:
                await self._evict_lru()
            
            # Set value
            self.memory_cache[key] = {
                "value": value,
                "expires_at": expires_at or datetime.now() + timedelta(seconds=self.ttl_seconds)
            }
            self.access_times[key] = time.time()
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to set in memory cache: {e}")
            return False
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            self.logger.logger.warning(f"Failed to get from Redis: {e}")
        
        return None
    
    async def _set_in_redis(
        self,
        key: str,
        value: Any,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Set value in Redis cache."""
        if not self.redis_client:
            return True  # Not an error if Redis is not available
        
        try:
            ttl = self.ttl_seconds
            if expires_at:
                ttl = int((expires_at - datetime.now()).total_seconds())
            
            await self.redis_client.setex(key, ttl, json.dumps(value))
            return True
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to set in Redis: {e}")
            return False
    
    async def _get_from_file(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check expiration
            expires_at = datetime.fromisoformat(data["expires_at"])
            if datetime.now() > expires_at:
                file_path.unlink()
                return None
            
            return data["value"]
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to get from file cache: {e}")
            return None
    
    async def _set_in_file(
        self,
        key: str,
        value: Any,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Set value in file cache."""
        file_path = self._get_file_path(key)
        
        try:
            data = {
                "value": value,
                "expires_at": (expires_at or datetime.now() + timedelta(seconds=self.ttl_seconds)).isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to set in file cache: {e}")
            return False
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash the key to create a safe filename
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_path / f"{hashed_key}.json"
    
    async def _evict_lru(self) -> None:
        """Evict least recently used item from memory cache."""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times, key=self.access_times.get)
        
        # Remove from caches
        self.memory_cache.pop(lru_key, None)
        self.access_times.pop(lru_key, None)
    
    async def close(self) -> None:
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close() 