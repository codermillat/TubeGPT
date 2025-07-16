"""
YouTube Data API v3 Client for AI SEO Assistant.

Cursor Rules:
- Use aiohttp for all HTTP operations
- Implement retry logic with exponential backoff
- Add rate limiting and quota management
- Cache responses appropriately
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import aiohttp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.core.exceptions import (
    YouTubeAPIException,
    YouTubeAuthenticationError,
    YouTubeQuotaExceededError,
    YouTubeVideoNotFoundError,
    YouTubeChannelNotFoundError,
    NetworkError,
    TimeoutError
)
from app.core.logging import ServiceLogger

# Initialize service logger
logger = ServiceLogger("youtube_client")

# YouTube API configuration
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

class YouTubeClient:
    """Async YouTube API client with OAuth authentication."""
    
    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize YouTube client.
        
        Args:
            credentials_file: Path to OAuth credentials file
            token_file: Path to token storage file
            session: Optional aiohttp session
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self.session = session
        self.logger = logger
        
        # API configuration
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.api_version = "v3"
        
        # Authentication
        self.credentials = None
        self.service = None
        
        # Rate limiting
        self.quota_used = 0
        self.quota_limit = settings.YOUTUBE_API_QUOTA_LIMIT
        self.request_times = []
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_window = 100
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0
        
        # Initialize token file directory
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth 2.0.
        
        Returns:
            True if authentication successful, False otherwise
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation("authenticate")
        
        try:
            bound_logger.info("Starting YouTube authentication")
            
            # Load existing credentials
            if self.token_file.exists():
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_file), SCOPES
                )
            
            # Refresh or obtain new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh expired credentials
                    self.credentials.refresh(Request())
                else:
                    # Get new credentials
                    if not self.credentials_file.exists():
                        raise YouTubeAuthenticationError(
                            f"Credentials file not found: {self.credentials_file}"
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            # Build service
            self.service = build('youtube', self.api_version, credentials=self.credentials)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "authenticate",
                duration_ms=duration_ms,
                result_summary={"authenticated": True}
            )
            
            return True
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "authenticate",
                error=e,
                duration_ms=duration_ms
            )
            raise YouTubeAuthenticationError(
                f"YouTube authentication failed: {str(e)}"
            ) from e
    
    async def get_channel_stats(self, channel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get channel statistics.
        
        Args:
            channel_id: Optional channel ID (defaults to authenticated user's channel)
            
        Returns:
            Channel statistics
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "get_channel_stats",
            channel_id=channel_id or "self"
        )
        
        try:
            bound_logger.info("Getting channel statistics")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            # Get channel details
            request_params = {
                'part': 'snippet,statistics,contentDetails',
                'id': channel_id
            } if channel_id else {
                'part': 'snippet,statistics,contentDetails',
                'mine': True
            }
            
            response = await self._make_api_request('channels', request_params)
            
            if not response.get('items'):
                raise YouTubeChannelNotFoundError(
                    f"Channel not found: {channel_id or 'authenticated user'}"
                )
            
            channel = response['items'][0]
            
            # Structure response
            result = {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'published_at': channel['snippet']['publishedAt'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'view_count': int(channel['statistics'].get('viewCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'uploads_playlist_id': channel['contentDetails']['relatedPlaylists']['uploads']
            }
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "get_channel_stats",
                duration_ms=duration_ms,
                result_summary={"subscriber_count": result['subscriber_count']},
                channel_id=channel_id or "self"
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "get_channel_stats",
                error=e,
                duration_ms=duration_ms,
                channel_id=channel_id or "self"
            )
            raise self._map_youtube_exception(e)
    
    async def get_latest_videos(
        self,
        channel_id: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get latest videos from channel.
        
        Args:
            channel_id: Optional channel ID
            max_results: Maximum number of videos to return
            
        Returns:
            List of video data
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "get_latest_videos",
            channel_id=channel_id or "self",
            max_results=max_results
        )
        
        try:
            bound_logger.info("Getting latest videos")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            # Get channel's upload playlist
            if not channel_id:
                channel_stats = await self.get_channel_stats()
                uploads_playlist_id = channel_stats['uploads_playlist_id']
            else:
                channel_stats = await self.get_channel_stats(channel_id)
                uploads_playlist_id = channel_stats['uploads_playlist_id']
            
            # Get videos from uploads playlist
            request_params = {
                'part': 'snippet,contentDetails',
                'playlistId': uploads_playlist_id,
                'maxResults': min(max_results, 50)
            }
            
            response = await self._make_api_request('playlistItems', request_params)
            
            # Get detailed video information
            video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]
            
            if not video_ids:
                return []
            
            videos_data = await self.get_videos_by_ids(video_ids)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "get_latest_videos",
                duration_ms=duration_ms,
                result_summary={"video_count": len(videos_data)},
                channel_id=channel_id or "self"
            )
            
            return videos_data
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "get_latest_videos",
                error=e,
                duration_ms=duration_ms,
                channel_id=channel_id or "self"
            )
            raise self._map_youtube_exception(e)
    
    async def get_video_by_id(self, video_id: str) -> Dict[str, Any]:
        """
        Get video details by ID.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video data
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "get_video_by_id",
            video_id=video_id
        )
        
        try:
            bound_logger.info("Getting video by ID")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            request_params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id
            }
            
            response = await self._make_api_request('videos', request_params)
            
            if not response.get('items'):
                raise YouTubeVideoNotFoundError(f"Video not found: {video_id}")
            
            video = response['items'][0]
            result = self._format_video_data(video)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "get_video_by_id",
                duration_ms=duration_ms,
                result_summary={"view_count": result.get('view_count', 0)},
                video_id=video_id
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "get_video_by_id",
                error=e,
                duration_ms=duration_ms,
                video_id=video_id
            )
            raise self._map_youtube_exception(e)
    
    async def get_videos_by_ids(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple videos by IDs.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of video data
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "get_videos_by_ids",
            video_count=len(video_ids)
        )
        
        try:
            bound_logger.info("Getting videos by IDs")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            # YouTube API supports up to 50 IDs per request
            batch_size = 50
            all_videos = []
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                request_params = {
                    'part': 'snippet,statistics,contentDetails',
                    'id': ','.join(batch_ids)
                }
                
                response = await self._make_api_request('videos', request_params)
                
                for video in response.get('items', []):
                    all_videos.append(self._format_video_data(video))
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "get_videos_by_ids",
                duration_ms=duration_ms,
                result_summary={"video_count": len(all_videos)},
                requested_count=len(video_ids)
            )
            
            return all_videos
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "get_videos_by_ids",
                error=e,
                duration_ms=duration_ms,
                video_count=len(video_ids)
            )
            raise self._map_youtube_exception(e)
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search for videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            order: Sort order (relevance, date, rating, viewCount, etc.)
            
        Returns:
            List of video data
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "search_videos",
            query=query[:50],
            max_results=max_results,
            order=order
        )
        
        try:
            bound_logger.info("Searching videos")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            # Search for videos
            request_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': min(max_results, 50),
                'order': order
            }
            
            response = await self._make_api_request('search', request_params)
            
            # Get detailed video information
            video_ids = [item['id']['videoId'] for item in response.get('items', [])]
            
            if not video_ids:
                return []
            
            videos_data = await self.get_videos_by_ids(video_ids)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "search_videos",
                duration_ms=duration_ms,
                result_summary={"video_count": len(videos_data)},
                query=query[:50]
            )
            
            return videos_data
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "search_videos",
                error=e,
                duration_ms=duration_ms,
                query=query[:50]
            )
            raise self._map_youtube_exception(e)
    
    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get video comments.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments
            
        Returns:
            List of comment data
        """
        start_time = time.time()
        
        bound_logger = self.logger.bind_operation(
            "get_video_comments",
            video_id=video_id,
            max_results=max_results
        )
        
        try:
            bound_logger.info("Getting video comments")
            
            await self._ensure_authenticated()
            await self._check_rate_limit()
            
            request_params = {
                'part': 'snippet',
                'videoId': video_id,
                'maxResults': min(max_results, 100),
                'order': 'relevance'
            }
            
            response = await self._make_api_request('commentThreads', request_params)
            
            comments = []
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'id': item['id'],
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'published_at': comment['publishedAt'],
                    'like_count': comment.get('likeCount', 0),
                    'reply_count': item['snippet'].get('totalReplyCount', 0)
                })
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_success(
                "get_video_comments",
                duration_ms=duration_ms,
                result_summary={"comment_count": len(comments)},
                video_id=video_id
            )
            
            return comments
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.log_operation_error(
                "get_video_comments",
                error=e,
                duration_ms=duration_ms,
                video_id=video_id
            )
            raise self._map_youtube_exception(e)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for YouTube client.
        
        Returns:
            Health check results
        """
        try:
            # Test authentication
            auth_success = await self.authenticate()
            
            # Test API call
            if auth_success:
                channel_stats = await self.get_channel_stats()
                api_success = bool(channel_stats)
            else:
                api_success = False
            
            return {
                "status": "healthy" if auth_success and api_success else "unhealthy",
                "authentication": auth_success,
                "api_access": api_success,
                "quota_used": self.quota_used,
                "quota_limit": self.quota_limit,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _ensure_authenticated(self):
        """Ensure client is authenticated."""
        if not self.credentials or not self.credentials.valid:
            await self.authenticate()
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Clean old requests
        cutoff_time = current_time - self.rate_limit_window
        self.request_times = [
            req_time for req_time in self.request_times
            if req_time > cutoff_time
        ]
        
        # Check rate limit
        if len(self.request_times) >= self.max_requests_per_window:
            raise YouTubeQuotaExceededError(
                f"Rate limit exceeded: {len(self.request_times)} requests in {self.rate_limit_window} seconds"
            )
        
        # Check quota
        if self.quota_used >= self.quota_limit:
            raise YouTubeQuotaExceededError(
                f"Daily quota exceeded: {self.quota_used}/{self.quota_limit}"
            )
        
        # Add current request
        self.request_times.append(current_time)
        self.quota_used += 1
    
    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Use the synchronous API in async context
                def _sync_request():
                    method = getattr(self.service, endpoint)()
                    return method.list(**params).execute()
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, _sync_request)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                
                # Wait before retry
                await asyncio.sleep(self.retry_delay * (self.backoff_factor ** attempt))
    
    def _format_video_data(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Format video data for consistent output."""
        snippet = video['snippet']
        statistics = video.get('statistics', {})
        
        return {
            'id': video['id'],
            'title': snippet['title'],
            'description': snippet['description'],
            'published_at': snippet['publishedAt'],
            'channel_id': snippet['channelId'],
            'channel_title': snippet['channelTitle'],
            'tags': snippet.get('tags', []),
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'dislike_count': int(statistics.get('dislikeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
            'duration': video.get('contentDetails', {}).get('duration', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
        }
    
    def _map_youtube_exception(self, e: Exception) -> YouTubeAPIException:
        """Map generic exceptions to YouTube-specific exceptions."""
        error_str = str(e).lower()
        
        if "quota" in error_str or "limit" in error_str:
            return YouTubeQuotaExceededError(str(e))
        elif "not found" in error_str or "404" in error_str:
            return YouTubeVideoNotFoundError(str(e))
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            return YouTubeAuthenticationError(str(e))
        elif "network" in error_str or "connection" in error_str:
            return NetworkError(str(e))
        elif "timeout" in error_str:
            return TimeoutError(str(e))
        else:
            return YouTubeAPIException(str(e))
    
    async def close(self):
        """Close client connections."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global instance for backward compatibility
youtube_client = None 