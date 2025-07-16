#!/usr/bin/env python3
"""
Competitor Scraper Module for YouTube Channel Analysis.

This module fetches competitor YouTube channel data using the YouTube Data API
to support gap analysis and competitive intelligence for content strategy.

Features:
1. YouTube Data API integration for public channel data
2. Automatic CSV export in gap_detector compatible format
3. Rate limiting and error handling
4. Batch processing for multiple competitors
5. Data validation and cleaning

Data Sources:
- YouTube Data API v3 (primary method)
- Public channel data only (no authentication required for public videos)
- Respects API quotas and rate limits
"""

import os
import csv
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create data directories
DATA_DIR = Path("data/competitors")
DATA_DIR.mkdir(parents=True, exist_ok=True)

class CompetitorScraper:
    """
    Scrapes competitor YouTube channel data for gap analysis.
    
    Uses YouTube Data API v3 to fetch public channel information including
    recent videos, view counts, and metadata for competitive analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Competitor Scraper.
        
        Args:
            api_key (str, optional): YouTube Data API key. Uses YOUTUBE_API_KEY env var if not provided.
        """
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            logger.warning(
                "YouTube API key not found. Some features may be limited. "
                "Set YOUTUBE_API_KEY environment variable for full functionality."
            )
        
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.session = requests.Session()
        
        # Rate limiting (YouTube API allows 10,000 units per day)
        self.requests_per_minute = 100
        self.last_request_time = 0
        self.request_count = 0
        
        logger.info("Competitor Scraper initialized")
    
    def _rate_limit(self):
        """Implement rate limiting to respect API quotas."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_request_time > 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Wait if we've hit the rate limit
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        self.request_count += 1
    
    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make a request to YouTube Data API with error handling.
        
        Args:
            endpoint (str): API endpoint (e.g., 'channels', 'search', 'videos')
            params (dict): Request parameters
            
        Returns:
            dict: API response data, or None if request failed
        """
        if not self.api_key:
            logger.error("YouTube API key required for this operation")
            return None
        
        self._rate_limit()
        
        params['key'] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"YouTube API error: {data['error']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid JSON response from {endpoint}: {e}")
            return None
    
    def _extract_channel_id(self, channel_input: str) -> Optional[str]:
        """
        Extract channel ID from various input formats.
        
        Args:
            channel_input (str): Channel URL, handle, or ID
            
        Returns:
            str: Channel ID, or None if not found
        """
        # If it's already a channel ID (starts with UC and 24 chars)
        if channel_input.startswith('UC') and len(channel_input) == 24:
            return channel_input
        
        # If it's a URL, extract the channel ID or handle
        if 'youtube.com' in channel_input:
            parsed = urlparse(channel_input)
            
            # Handle /channel/UC... format
            if '/channel/' in parsed.path:
                channel_id = parsed.path.split('/channel/')[-1].split('/')[0]
                if channel_id.startswith('UC') and len(channel_id) == 24:
                    return channel_id
            
            # Handle /@username format
            elif '/@' in parsed.path:
                username = parsed.path.split('/@')[-1].split('/')[0]
                return self._get_channel_id_by_handle(username)
            
            # Handle /c/username or /user/username format
            elif '/c/' in parsed.path or '/user/' in parsed.path:
                username = parsed.path.split('/')[-1]
                return self._get_channel_id_by_username(username)
        
        # Try as username/handle
        return self._get_channel_id_by_handle(channel_input)
    
    def _get_channel_id_by_handle(self, handle: str) -> Optional[str]:
        """Get channel ID by handle/username using search API."""
        if not self.api_key:
            return None
        
        # Remove @ if present
        handle = handle.lstrip('@')
        
        params = {
            'part': 'snippet',
            'type': 'channel',
            'q': handle,
            'maxResults': 5
        }
        
        data = self._make_api_request('search', params)
        if not data or 'items' not in data:
            return None
        
        # Look for exact match
        for item in data['items']:
            if item['snippet']['title'].lower() == handle.lower():
                return item['snippet']['channelId']
        
        # Return first result if no exact match
        if data['items']:
            return data['items'][0]['snippet']['channelId']
        
        return None
    
    def _get_channel_id_by_username(self, username: str) -> Optional[str]:
        """Get channel ID by legacy username."""
        if not self.api_key:
            return None
        
        params = {
            'part': 'id',
            'forUsername': username
        }
        
        data = self._make_api_request('channels', params)
        if data and 'items' in data and data['items']:
            return data['items'][0]['id']
        
        return None
    
    def fetch_competitor_videos(self, channel_input: str, max_videos: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent videos from a competitor channel.
        
        Args:
            channel_input (str): Channel URL, handle, or ID
            max_videos (int): Maximum number of videos to fetch
            
        Returns:
            List[Dict]: List of video data dictionaries
            
        Raises:
            ValueError: If channel not found or API unavailable
            Exception: If API request fails
        """
        try:
            logger.info(f"Fetching videos for channel: {channel_input}")
            
            # Extract channel ID
            channel_id = self._extract_channel_id(channel_input)
            if not channel_id:
                raise ValueError(f"Could not extract channel ID from: {channel_input}")
            
            logger.info(f"Resolved channel ID: {channel_id}")
            
            # Get channel info first
            channel_info = self._get_channel_info(channel_id)
            if not channel_info:
                raise ValueError(f"Channel not found: {channel_id}")
            
            # Get uploads playlist ID
            uploads_playlist_id = channel_info.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            if not uploads_playlist_id:
                raise ValueError(f"Could not find uploads playlist for channel: {channel_id}")
            
            # Fetch videos from uploads playlist
            videos = []
            next_page_token = None
            
            while len(videos) < max_videos:
                params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': uploads_playlist_id,
                    'maxResults': min(50, max_videos - len(videos))
                }
                
                if next_page_token:
                    params['pageToken'] = next_page_token
                
                data = self._make_api_request('playlistItems', params)
                if not data or 'items' not in data:
                    break
                
                # Extract video IDs for statistics
                video_ids = [item['contentDetails']['videoId'] for item in data['items']]
                video_stats = self._get_video_statistics(video_ids)
                
                # Process videos
                for item in data['items']:
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    stats = video_stats.get(video_id, {})
                    
                    video_data = {
                        'videoId': video_id,
                        'videoTitle': snippet.get('title', ''),
                        'description': snippet.get('description', '')[:500],  # Truncate description
                        'publishedAt': snippet.get('publishedAt', ''),
                        'date': self._format_date(snippet.get('publishedAt', '')),
                        'views': int(stats.get('viewCount', 0)),
                        'likes': int(stats.get('likeCount', 0)),
                        'comments': int(stats.get('commentCount', 0)),
                        'channelId': channel_id,
                        'channelTitle': channel_info.get('snippet', {}).get('title', ''),
                        # Add placeholder values for gap_detector compatibility
                        'impressions': int(stats.get('viewCount', 0)) * 10,  # Estimate
                        'CTR': 0.05,  # Default estimate
                        'averageViewDuration': 120,  # Default estimate
                        'country': 'Unknown'
                    }
                    
                    videos.append(video_data)
                
                # Check for next page
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Successfully fetched {len(videos)} videos from {channel_info.get('snippet', {}).get('title', 'Unknown')}")
            return videos[:max_videos]
            
        except Exception as e:
            logger.error(f"Error fetching competitor videos: {e}")
            raise
    
    def _get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get basic channel information."""
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': channel_id
        }
        
        data = self._make_api_request('channels', params)
        if data and 'items' in data and data['items']:
            return data['items'][0]
        
        return None
    
    def _get_video_statistics(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get statistics for multiple videos."""
        if not video_ids:
            return {}
        
        # Process in batches of 50 (API limit)
        all_stats = {}
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            params = {
                'part': 'statistics',
                'id': ','.join(batch_ids)
            }
            
            data = self._make_api_request('videos', params)
            if data and 'items' in data:
                for item in data['items']:
                    video_id = item['id']
                    stats = item.get('statistics', {})
                    all_stats[video_id] = stats
        
        return all_stats
    
    def _format_date(self, iso_date: str) -> str:
        """Convert ISO date to YYYY-MM-DD format."""
        try:
            if iso_date:
                dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        return datetime.now().strftime('%Y-%m-%d')
    
    def save_competitor_data(self, channel_input: str, max_videos: int = 20, 
                           output_csv: Optional[str] = None) -> str:
        """
        Fetch competitor data and save to CSV file.
        
        Args:
            channel_input (str): Channel URL, handle, or ID
            max_videos (int): Maximum number of videos to fetch
            output_csv (str, optional): Custom output filename
            
        Returns:
            str: Path to saved CSV file
            
        Raises:
            Exception: If fetching or saving fails
        """
        try:
            # Fetch video data
            videos = self.fetch_competitor_videos(channel_input, max_videos)
            
            if not videos:
                raise ValueError("No videos found for the specified channel")
            
            # Generate output filename if not provided
            if not output_csv:
                # Clean channel name for filename
                channel_name = videos[0]['channelTitle']
                clean_name = re.sub(r'[^\w\s-]', '', channel_name).strip()
                clean_name = re.sub(r'[-\s]+', '_', clean_name).lower()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_csv = f"competitor_{clean_name}_{timestamp}.csv"
            
            # Ensure output is in competitors directory
            output_path = DATA_DIR / output_csv
            
            # Save to CSV
            df = pd.DataFrame(videos)
            
            # Reorder columns to match gap_detector expectations
            column_order = [
                'videoId', 'videoTitle', 'date', 'views', 'impressions', 
                'CTR', 'averageViewDuration', 'country', 'channelId', 
                'channelTitle', 'publishedAt', 'description', 'likes', 'comments'
            ]
            
            # Only include columns that exist
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
            
            df.to_csv(output_path, index=False)
            
            logger.info(f"Saved {len(videos)} videos to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving competitor data: {e}")
            raise

def fetch_multiple_competitors(competitor_channels: List[str], max_videos: int = 20) -> Dict[str, str]:
    """
    Fetch data for multiple competitor channels.
    
    Args:
        competitor_channels (List[str]): List of channel URLs, handles, or IDs
        max_videos (int): Maximum videos per channel
        
    Returns:
        Dict[str, str]: Mapping of channel input to saved CSV path
    """
    scraper = CompetitorScraper()
    results = {}
    
    for channel in competitor_channels:
        try:
            logger.info(f"Processing competitor: {channel}")
            csv_path = scraper.save_competitor_data(channel, max_videos)
            results[channel] = csv_path
            
            # Small delay between channels to be respectful
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to process {channel}: {e}")
            results[channel] = None
    
    return results

def main():
    """
    Example usage of the Competitor Scraper.
    """
    try:
        # Example competitor channels
        competitors = [
            "https://www.youtube.com/@MrBeast",  # URL format
            "@PewDiePie",  # Handle format
            "UC-lHJZR3Gqxm24_Vd_AJ5Yw"  # Channel ID format
        ]
        
        print("YouTube Competitor Scraper")
        print("=" * 40)
        
        # Check API key
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            print("Warning: YOUTUBE_API_KEY not found in environment variables.")
            print("Some features may be limited. Please set your YouTube Data API key.")
            print()
        
        # Initialize scraper
        scraper = CompetitorScraper()
        
        # Example: Fetch single competitor
        print("Fetching single competitor example...")
        try:
            videos = scraper.fetch_competitor_videos(competitors[0], max_videos=5)
            print(f"Found {len(videos)} videos")
            
            if videos:
                print("Sample video:")
                sample = videos[0]
                print(f"  Title: {sample['videoTitle']}")
                print(f"  Views: {sample['views']:,}")
                print(f"  Date: {sample['date']}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        print()
        
        # Example: Save competitor data
        print("Saving competitor data example...")
        try:
            csv_path = scraper.save_competitor_data(competitors[0], max_videos=10)
            print(f"Saved to: {csv_path}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        print()
        
        # Example: Multiple competitors
        print("Processing multiple competitors...")
        results = fetch_multiple_competitors(competitors[:2], max_videos=5)
        
        for channel, csv_path in results.items():
            if csv_path:
                print(f"✓ {channel} → {csv_path}")
            else:
                print(f"✗ {channel} → Failed")
        
        print(f"\nAll competitor data saved in: {DATA_DIR}")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()