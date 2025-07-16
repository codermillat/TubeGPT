"""
Memory Service for YouTube SEO Assistant.

Cursor Rules:
- Use dependency injection for all external dependencies
- Implement proper async/await patterns
- Add comprehensive error handling with structured logging
- Write tests for all public methods
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import RLock

from app.core.config import settings
from app.core.exceptions import StorageException
from app.core.logging import ServiceLogger
from app.utils.time_utils import TimeTracker

# Initialize service logger
logger = ServiceLogger("memory_service")


class MemoryService:
    """Local file-based memory service for strategy storage."""
    
    def __init__(self, storage_path: str):
        """
        Initialize memory service.
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path)
        self.logger = logger
        self.time_tracker = TimeTracker()
        
        # Thread-safe operations
        self._lock = RLock()
        
        # Initialize storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Cache for recently accessed files
        self._file_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 100
        self._cache_ttl = 300  # 5 minutes
    
    async def save_strategy(
        self,
        conversation_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Save strategy conversation to local storage.
        
        Args:
            conversation_data: Strategy conversation data
            filename: Optional filename (generates if not provided)
            
        Returns:
            Filename of saved strategy
            
        Raises:
            StorageException: If save fails
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "save_strategy",
            has_filename=filename is not None,
            data_keys=list(conversation_data.keys())
        )
        
        try:
            bound_logger.info("Starting strategy save")
            
            with self._lock:
                # Generate filename if not provided
                if not filename:
                    timestamp = self.time_tracker.get_timestamp()
                    filename = f"{timestamp}_strategy.json"
                
                # Ensure .json extension
                if not filename.endswith('.json'):
                    filename += '.json'
                
                # Prepare data with metadata
                strategy_data = {
                    "id": filename.replace('.json', ''),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "type": "strategy",
                    "data": conversation_data
                }
                
                # Save to file
                file_path = self.storage_path / filename
                
                # Create backup if file exists
                if file_path.exists():
                    backup_path = file_path.with_suffix('.json.backup')
                    file_path.rename(backup_path)
                
                # Write new file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(strategy_data, f, indent=2, ensure_ascii=False)
                
                # Update cache
                self._update_cache(filename, strategy_data)
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "save_strategy",
                    duration_ms=duration_ms,
                    result_summary={"filename": filename, "size": len(json.dumps(strategy_data))},
                    filename=filename
                )
                
                return filename
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "save_strategy",
                error=e,
                duration_ms=duration_ms,
                filename=filename
            )
            raise StorageException(
                f"Failed to save strategy: {str(e)}",
                context={"filename": filename}
            ) from e
    
    async def load_strategy(self, filename: str) -> Dict[str, Any]:
        """
        Load strategy from local storage.
        
        Args:
            filename: Strategy filename
            
        Returns:
            Strategy data
            
        Raises:
            StorageException: If load fails
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "load_strategy",
            filename=filename
        )
        
        try:
            bound_logger.info("Starting strategy load")
            
            with self._lock:
                # Check cache first
                cached_data = self._get_from_cache(filename)
                if cached_data:
                    bound_logger.info("Cache hit for strategy")
                    return cached_data
                
                # Load from file
                file_path = self.storage_path / filename
                
                if not file_path.exists():
                    raise StorageException(
                        f"Strategy file not found: {filename}",
                        context={"filename": filename}
                    )
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                
                # Update cache
                self._update_cache(filename, strategy_data)
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "load_strategy",
                    duration_ms=duration_ms,
                    result_summary={"filename": filename, "has_data": bool(strategy_data)},
                    filename=filename
                )
                
                return strategy_data
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "load_strategy",
                error=e,
                duration_ms=duration_ms,
                filename=filename
            )
            raise StorageException(
                f"Failed to load strategy: {str(e)}",
                context={"filename": filename}
            ) from e
    
    async def list_strategies(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all stored strategies.
        
        Args:
            limit: Optional limit on number of results
            offset: Offset for pagination
            
        Returns:
            List of strategy metadata
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "list_strategies",
            limit=limit,
            offset=offset
        )
        
        try:
            bound_logger.info("Starting strategy list")
            
            with self._lock:
                # Get all JSON files
                json_files = list(self.storage_path.glob("*.json"))
                
                # Filter out backup files
                json_files = [f for f in json_files if not f.name.endswith('.backup')]
                
                # Sort by modification time (newest first)
                json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                
                # Apply pagination
                if offset > 0:
                    json_files = json_files[offset:]
                
                if limit:
                    json_files = json_files[:limit]
                
                # Load metadata for each file
                strategies = []
                for file_path in json_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extract metadata
                        metadata = {
                            "id": data.get("id", file_path.stem),
                            "filename": file_path.name,
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "type": data.get("type", "strategy"),
                            "version": data.get("version", "1.0"),
                            "size": file_path.stat().st_size,
                            "title": self._extract_title(data.get("data", {}))
                        }
                        
                        strategies.append(metadata)
                        
                    except Exception as e:
                        bound_logger.logger.warning(
                            f"Failed to load metadata for {file_path.name}: {e}"
                        )
                        continue
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "list_strategies",
                    duration_ms=duration_ms,
                    result_summary={"count": len(strategies)},
                    limit=limit,
                    offset=offset
                )
                
                return strategies
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "list_strategies",
                error=e,
                duration_ms=duration_ms,
                limit=limit,
                offset=offset
            )
            raise StorageException(
                f"Failed to list strategies: {str(e)}"
            ) from e
    
    async def delete_strategy(self, filename: str) -> bool:
        """
        Delete strategy from storage.
        
        Args:
            filename: Strategy filename
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "delete_strategy",
            filename=filename
        )
        
        try:
            bound_logger.info("Starting strategy delete")
            
            with self._lock:
                file_path = self.storage_path / filename
                
                if not file_path.exists():
                    bound_logger.logger.warning(f"Strategy file not found: {filename}")
                    return False
                
                # Create backup before deletion
                backup_path = file_path.with_suffix('.json.deleted')
                file_path.rename(backup_path)
                
                # Remove from cache
                self._remove_from_cache(filename)
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "delete_strategy",
                    duration_ms=duration_ms,
                    result_summary={"deleted": True},
                    filename=filename
                )
                
                return True
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "delete_strategy",
                error=e,
                duration_ms=duration_ms,
                filename=filename
            )
            return False
    
    async def search_strategies(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search strategies by content.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of matching strategies
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "search_strategies",
            query=query[:50],
            max_results=max_results
        )
        
        try:
            bound_logger.info("Starting strategy search")
            
            with self._lock:
                # Get all strategies
                all_strategies = await self.list_strategies()
                
                # Filter by query
                matching_strategies = []
                query_lower = query.lower()
                
                for strategy_meta in all_strategies:
                    try:
                        # Load full strategy data
                        strategy_data = await self.load_strategy(strategy_meta["filename"])
                        
                        # Search in title and content
                        title = strategy_meta.get("title", "").lower()
                        content = json.dumps(strategy_data.get("data", {})).lower()
                        
                        if query_lower in title or query_lower in content:
                            strategy_meta["relevance_score"] = self._calculate_relevance(
                                query_lower, title, content
                            )
                            matching_strategies.append(strategy_meta)
                            
                    except Exception as e:
                        bound_logger.logger.warning(
                            f"Failed to search strategy {strategy_meta['filename']}: {e}"
                        )
                        continue
                
                # Sort by relevance
                matching_strategies.sort(
                    key=lambda x: x.get("relevance_score", 0),
                    reverse=True
                )
                
                # Limit results
                matching_strategies = matching_strategies[:max_results]
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "search_strategies",
                    duration_ms=duration_ms,
                    result_summary={"matches": len(matching_strategies)},
                    query=query[:50]
                )
                
                return matching_strategies
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "search_strategies",
                error=e,
                duration_ms=duration_ms,
                query=query[:50]
            )
            raise StorageException(
                f"Failed to search strategies: {str(e)}"
            ) from e
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics
        """
        try:
            with self._lock:
                json_files = list(self.storage_path.glob("*.json"))
                json_files = [f for f in json_files if not f.name.endswith('.backup')]
                
                total_size = sum(f.stat().st_size for f in json_files)
                
                return {
                    "total_strategies": len(json_files),
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "storage_path": str(self.storage_path),
                    "cache_size": len(self._file_cache),
                    "timestamp": time.time()
                }
                
        except Exception as e:
            raise StorageException(
                f"Failed to get storage stats: {str(e)}"
            ) from e
    
    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Clean up old backup and deleted files.
        
        Args:
            days: Files older than this will be deleted
            
        Returns:
            Number of files cleaned up
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "cleanup_old_files",
            days=days
        )
        
        try:
            bound_logger.info("Starting cleanup")
            
            with self._lock:
                cleanup_count = 0
                cutoff_time = time.time() - (days * 24 * 60 * 60)
                
                # Find old backup and deleted files
                patterns = ["*.backup", "*.deleted"]
                
                for pattern in patterns:
                    for file_path in self.storage_path.glob(pattern):
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            cleanup_count += 1
                
                duration_ms = (time.time() - start_time) * 1000
                self.logger.log_operation_success(
                    "cleanup_old_files",
                    duration_ms=duration_ms,
                    result_summary={"cleaned_up": cleanup_count},
                    days=days
                )
                
                return cleanup_count
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "cleanup_old_files",
                error=e,
                duration_ms=duration_ms,
                days=days
            )
            raise StorageException(
                f"Failed to cleanup old files: {str(e)}"
            ) from e
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for memory service.
        
        Returns:
            Health check results
        """
        try:
            # Test storage directory
            storage_accessible = self.storage_path.exists() and self.storage_path.is_dir()
            
            # Test write/read operations
            test_filename = "health_check_test.json"
            test_data = {"test": "data", "timestamp": time.time()}
            
            write_success = False
            read_success = False
            
            try:
                await self.save_strategy(test_data, test_filename)
                write_success = True
                
                loaded_data = await self.load_strategy(test_filename)
                read_success = loaded_data.get("data", {}).get("test") == "data"
                
                # Cleanup test file
                await self.delete_strategy(test_filename)
                
            except Exception:
                pass
            
            # Get storage stats
            stats = await self.get_storage_stats()
            
            return {
                "status": "healthy" if storage_accessible and write_success and read_success else "unhealthy",
                "storage_accessible": storage_accessible,
                "write_test": write_success,
                "read_test": read_success,
                "storage_stats": stats,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _update_cache(self, filename: str, data: Dict[str, Any]) -> None:
        """Update file cache."""
        # Remove oldest entries if cache is full
        if len(self._file_cache) >= self._cache_max_size:
            oldest_key = min(
                self._file_cache.keys(),
                key=lambda k: self._file_cache[k]["accessed_at"]
            )
            del self._file_cache[oldest_key]
        
        # Add/update entry
        self._file_cache[filename] = {
            "data": data,
            "cached_at": time.time(),
            "accessed_at": time.time()
        }
    
    def _get_from_cache(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get data from cache."""
        if filename not in self._file_cache:
            return None
        
        entry = self._file_cache[filename]
        
        # Check if expired
        if time.time() - entry["cached_at"] > self._cache_ttl:
            del self._file_cache[filename]
            return None
        
        # Update access time
        entry["accessed_at"] = time.time()
        
        return entry["data"]
    
    def _remove_from_cache(self, filename: str) -> None:
        """Remove data from cache."""
        self._file_cache.pop(filename, None)
    
    def _extract_title(self, data: Dict[str, Any]) -> str:
        """Extract title from strategy data."""
        # Try to extract meaningful title from data
        if "question" in data:
            return data["question"][:50] + "..." if len(data["question"]) > 50 else data["question"]
        elif "title" in data:
            return data["title"]
        elif "messages" in data and data["messages"]:
            first_message = data["messages"][0]
            if isinstance(first_message, dict) and "content" in first_message:
                content = first_message["content"][:50]
                return content + "..." if len(content) == 50 else content
        
        return "Untitled Strategy"
    
    def _calculate_relevance(self, query: str, title: str, content: str) -> float:
        """Calculate relevance score for search."""
        score = 0.0
        
        # Title matches have higher weight
        if query in title:
            score += 10.0
        
        # Content matches
        content_matches = content.count(query)
        score += content_matches * 1.0
        
        # Boost for exact phrase matches
        if query in content:
            score += 5.0
        
        return score 