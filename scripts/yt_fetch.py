import os
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeAnalyticsFetcher:
    """
    A class to fetch YouTube channel analytics data using OAuth2 authentication.
    Retrieves video metadata and analytics data, storing results in CSV format.
    """
    
    # OAuth2 scopes required for YouTube Data API and Analytics API
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/yt-analytics.readonly'
    ]
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize the YouTube Analytics Fetcher.
        
        Args:
            credentials_file (str): Path to OAuth2 credentials JSON file
            token_file (str): Path to store/retrieve access tokens
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube_service = None
        self.analytics_service = None
        self.channel_id = None
        
    def authenticate(self):
        """
        Authenticate with YouTube APIs using OAuth2.
        Creates or refreshes access tokens as needed.
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed existing credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Obtained new credentials")
            
            # Save credentials for future use
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build service objects
        self.youtube_service = build('youtube', 'v3', credentials=creds)
        self.analytics_service = build('youtubeAnalytics', 'v2', credentials=creds)
        
        # Get channel ID
        self._get_channel_id()
        logger.info(f"Successfully authenticated for channel: {self.channel_id}")
    
    def _get_channel_id(self):
        """Get the authenticated user's channel ID."""
        try:
            request = self.youtube_service.channels().list(
                part='id,snippet',
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                self.channel_id = response['items'][0]['id']
                channel_title = response['items'][0]['snippet']['title']
                logger.info(f"Found channel: {channel_title}")
            else:
                raise ValueError("No channel found for authenticated user")
                
        except HttpError as e:
            logger.error(f"Error getting channel ID: {e}")
            raise
    
    def get_video_list(self, days_back=30, max_results=50):
        """
        Get list of videos from the channel within specified timeframe.
        
        Args:
            days_back (int): Number of days back to fetch videos
            max_results (int): Maximum number of videos to retrieve
            
        Returns:
            list: List of video dictionaries with basic metadata
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get uploads playlist ID
            channel_request = self.youtube_service.channels().list(
                part='contentDetails',
                id=self.channel_id
            )
            channel_response = channel_request.execute()
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_request = self.youtube_service.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                playlist_response = playlist_request.execute()
                
                for item in playlist_response['items']:
                    video_date = datetime.strptime(
                        item['snippet']['publishedAt'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    )
                    
                    # Only include videos within our date range
                    if start_date <= video_date <= end_date:
                        videos.append({
                            'videoId': item['contentDetails']['videoId'],
                            'videoTitle': item['snippet']['title'],
                            'date': video_date.strftime('%Y-%m-%d'),
                            'publishedAt': item['snippet']['publishedAt']
                        })
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Retrieved {len(videos)} videos from the last {days_back} days")
            return videos[:max_results]
            
        except HttpError as e:
            logger.error(f"Error fetching video list: {e}")
            raise
    
    def get_video_stats(self, video_ids):
        """
        Get detailed statistics for videos using YouTube Data API.
        
        Args:
            video_ids (list): List of video IDs
            
        Returns:
            dict: Dictionary mapping video IDs to their statistics
        """
        try:
            video_stats = {}
            
            # Process videos in batches of 50 (API limit)
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                
                request = self.youtube_service.videos().list(
                    part='statistics',
                    id=','.join(batch_ids)
                )
                response = request.execute()
                
                for item in response['items']:
                    video_id = item['id']
                    stats = item['statistics']
                    video_stats[video_id] = {
                        'views': int(stats.get('viewCount', 0)),
                        'likes': int(stats.get('likeCount', 0)),
                        'comments': int(stats.get('commentCount', 0))
                    }
            
            return video_stats
            
        except HttpError as e:
            logger.error(f"Error fetching video statistics: {e}")
            raise
    
    def get_analytics_data(self, video_ids, start_date, end_date):
        """
        Get analytics data for videos using YouTube Analytics API.
        
        Args:
            video_ids (list): List of video IDs
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            dict: Dictionary mapping video IDs to their analytics data
        """
        try:
            analytics_data = {}
            
            # Get analytics for each video individually
            for video_id in video_ids:
                try:
                    request = self.analytics_service.reports().query(
                        ids=f'channel=={self.channel_id}',
                        startDate=start_date,
                        endDate=end_date,
                        metrics='impressions,impressionClickThroughRate,averageViewDuration',
                        dimensions='video,country',
                        filters=f'video=={video_id}',
                        sort='country'
                    )
                    response = request.execute()
                    
                    if response.get('rows'):
                        # Aggregate data by country
                        country_data = {}
                        total_impressions = 0
                        weighted_ctr = 0
                        weighted_avg_duration = 0
                        
                        for row in response['rows']:
                            country = row[1] if len(row) > 1 else 'Unknown'
                            impressions = row[2] if len(row) > 2 else 0
                            ctr = row[3] if len(row) > 3 else 0
                            avg_duration = row[4] if len(row) > 4 else 0
                            
                            country_data[country] = {
                                'impressions': impressions,
                                'ctr': ctr,
                                'avg_duration': avg_duration
                            }
                            
                            total_impressions += impressions
                            weighted_ctr += ctr * impressions
                            weighted_avg_duration += avg_duration * impressions
                        
                        # Calculate overall metrics
                        overall_ctr = weighted_ctr / total_impressions if total_impressions > 0 else 0
                        overall_avg_duration = weighted_avg_duration / total_impressions if total_impressions > 0 else 0
                        
                        analytics_data[video_id] = {
                            'impressions': total_impressions,
                            'CTR': round(overall_ctr, 4),
                            'averageViewDuration': round(overall_avg_duration, 2),
                            'country_data': country_data,
                            'top_country': max(country_data.keys(), key=lambda x: country_data[x]['impressions']) if country_data else 'Unknown'
                        }
                    else:
                        # Default values if no analytics data available
                        analytics_data[video_id] = {
                            'impressions': 0,
                            'CTR': 0.0,
                            'averageViewDuration': 0.0,
                            'country_data': {},
                            'top_country': 'Unknown'
                        }
                        
                except HttpError as e:
                    logger.warning(f"Error fetching analytics for video {video_id}: {e}")
                    analytics_data[video_id] = {
                        'impressions': 0,
                        'CTR': 0.0,
                        'averageViewDuration': 0.0,
                        'country_data': {},
                        'top_country': 'Unknown'
                    }
            
            return analytics_data
            
        except HttpError as e:
            logger.error(f"Error fetching analytics data: {e}")
            raise
    
    def fetch_and_save_data(self, days_back=30, max_results=50, output_file='yt_analytics.csv'):
        """
        Main method to fetch all data and save to CSV.
        
        Args:
            days_back (int): Number of days back to fetch data
            max_results (int): Maximum number of videos to process
            output_file (str): Output CSV file path
        """
        try:
            logger.info(f"Starting data fetch for last {days_back} days")
            
            # Get video list
            videos = self.get_video_list(days_back, max_results)
            
            if not videos:
                logger.warning("No videos found in the specified timeframe")
                return
            
            video_ids = [video['videoId'] for video in videos]
            
            # Get video statistics
            logger.info("Fetching video statistics...")
            video_stats = self.get_video_stats(video_ids)
            
            # Get analytics data
            logger.info("Fetching analytics data...")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            analytics_data = self.get_analytics_data(video_ids, start_date, end_date)
            
            # Combine all data
            combined_data = []
            for video in videos:
                video_id = video['videoId']
                stats = video_stats.get(video_id, {})
                analytics = analytics_data.get(video_id, {})
                
                row = {
                    'videoId': video_id,
                    'videoTitle': video['videoTitle'],
                    'date': video['date'],
                    'views': stats.get('views', 0),
                    'impressions': analytics.get('impressions', 0),
                    'CTR': analytics.get('CTR', 0.0),
                    'averageViewDuration': analytics.get('averageViewDuration', 0.0),
                    'country': analytics.get('top_country', 'Unknown')
                }
                combined_data.append(row)
            
            # Save to CSV
            self._save_to_csv(combined_data, output_file)
            logger.info(f"Successfully saved {len(combined_data)} records to {output_file}")
            
        except Exception as e:
            logger.error(f"Error in fetch_and_save_data: {e}")
            raise
    
    def _save_to_csv(self, data, filename):
        """
        Save data to CSV file.
        
        Args:
            data (list): List of dictionaries containing video data
            filename (str): Output CSV filename
        """
        try:
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            
            # Also save with timestamp for historical tracking
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"yt_analytics_backup_{timestamp}.csv"
            df.to_csv(backup_filename, index=False)
            
            logger.info(f"Data saved to {filename} and backup created: {backup_filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            raise


def main():
    """
    Main function to run the YouTube Analytics Fetcher.
    Modify these parameters as needed for your use case.
    """
    try:
        # Initialize fetcher
        fetcher = YouTubeAnalyticsFetcher()
        
        # Authenticate
        fetcher.authenticate()
        
        # Fetch and save data
        # Adjust days_back and max_results as needed
        fetcher.fetch_and_save_data(
            days_back=30,           # Last 30 days
            max_results=50,         # Max 50 videos
            output_file='yt_analytics.csv'
        )
        
    except FileNotFoundError as e:
        logger.error(f"Setup required: {e}")
        print("\nSETUP INSTRUCTIONS:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select existing one")
        print("3. Enable YouTube Data API v3 and YouTube Analytics API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the credentials JSON file and save as 'credentials.json'")
        print("6. Run this script again")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()