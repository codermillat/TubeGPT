"""
Unit tests for competitor_scraper.py module.

Tests competitor data fetching with mocked YouTube API responses
to avoid hitting real APIs during testing.
"""

import pytest
import json
import tempfile
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import requests

# Import the module to test
from competitor_scraper import (
    CompetitorScraper,
    fetch_multiple_competitors
)

# Mock API responses for testing
MOCK_CHANNEL_RESPONSE = {
    "items": [{
        "id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
        "snippet": {
            "title": "Test Channel",
            "description": "Test channel description"
        },
        "contentDetails": {
            "relatedPlaylists": {
                "uploads": "UU-lHJZR3Gqxm24_Vd_AJ5Yw"
            }
        },
        "statistics": {
            "subscriberCount": "100000",
            "videoCount": "500"
        }
    }]
}

MOCK_PLAYLIST_RESPONSE = {
    "items": [
        {
            "snippet": {
                "title": "Test Video 1",
                "description": "Test description 1",
                "publishedAt": "2024-01-15T10:00:00Z"
            },
            "contentDetails": {
                "videoId": "test_video_1"
            }
        },
        {
            "snippet": {
                "title": "Test Video 2",
                "description": "Test description 2",
                "publishedAt": "2024-01-14T15:30:00Z"
            },
            "contentDetails": {
                "videoId": "test_video_2"
            }
        }
    ],
    "nextPageToken": None
}

MOCK_VIDEO_STATS_RESPONSE = {
    "items": [
        {
            "id": "test_video_1",
            "statistics": {
                "viewCount": "50000",
                "likeCount": "1500",
                "commentCount": "200"
            }
        },
        {
            "id": "test_video_2",
            "statistics": {
                "viewCount": "30000",
                "likeCount": "900",
                "commentCount": "150"
            }
        }
    ]
}

MOCK_SEARCH_RESPONSE = {
    "items": [{
        "snippet": {
            "channelId": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            "title": "Test Channel"
        }
    }]
}

class TestCompetitorScraper:
    """Test suite for CompetitorScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create CompetitorScraper instance for testing."""
        return CompetitorScraper(api_key='test_api_key')
    
    @pytest.fixture
    def scraper_no_key(self):
        """Create CompetitorScraper without API key."""
        return CompetitorScraper()
    
    def test_scraper_initialization_with_key(self, scraper):
        """Test scraper initialization with API key."""
        assert scraper.api_key == 'test_api_key'
        assert scraper.base_url == "https://www.googleapis.com/youtube/v3"
        assert scraper.requests_per_minute == 100
    
    def test_scraper_initialization_no_key(self, scraper_no_key):
        """Test scraper initialization without API key."""
        assert scraper_no_key.api_key is None
    
    def test_extract_channel_id_from_id(self, scraper):
        """Test channel ID extraction from channel ID."""
        channel_id = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        result = scraper._extract_channel_id(channel_id)
        assert result == channel_id
    
    def test_extract_channel_id_from_url(self, scraper):
        """Test channel ID extraction from URL."""
        url = "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        result = scraper._extract_channel_id(url)
        assert result == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    def test_extract_channel_id_from_handle(self, mock_api, scraper):
        """Test channel ID extraction from handle."""
        mock_api.return_value = MOCK_SEARCH_RESPONSE
        
        result = scraper._extract_channel_id("@testchannel")
        
        assert result == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        mock_api.assert_called_once_with('search', {
            'part': 'snippet',
            'type': 'channel',
            'q': 'testchannel',
            'maxResults': 5
        })
    
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    def test_get_channel_info_success(self, mock_api, scraper):
        """Test successful channel info retrieval."""
        mock_api.return_value = MOCK_CHANNEL_RESPONSE
        
        result = scraper._get_channel_info("UC-lHJZR3Gqxm24_Vd_AJ5Yw")
        
        assert result is not None
        assert result['id'] == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        assert result['snippet']['title'] == "Test Channel"
    
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    def test_get_channel_info_not_found(self, mock_api, scraper):
        """Test channel info retrieval when channel not found."""
        mock_api.return_value = {"items": []}
        
        result = scraper._get_channel_info("invalid_channel_id")
        
        assert result is None
    
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    def test_get_video_statistics(self, mock_api, scraper):
        """Test video statistics retrieval."""
        mock_api.return_value = MOCK_VIDEO_STATS_RESPONSE
        
        video_ids = ["test_video_1", "test_video_2"]
        result = scraper._get_video_statistics(video_ids)
        
        assert len(result) == 2
        assert result["test_video_1"]["viewCount"] == "50000"
        assert result["test_video_2"]["viewCount"] == "30000"
    
    def test_format_date(self, scraper):
        """Test date formatting."""
        iso_date = "2024-01-15T10:00:00Z"
        result = scraper._format_date(iso_date)
        assert result == "2024-01-15"
        
        # Test invalid date
        result = scraper._format_date("invalid_date")
        assert len(result) == 10  # Should return current date in YYYY-MM-DD format
    
    @patch('competitor_scraper.CompetitorScraper._get_video_statistics')
    @patch('competitor_scraper.CompetitorScraper._get_channel_info')
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    @patch('competitor_scraper.CompetitorScraper._extract_channel_id')
    def test_fetch_competitor_videos_success(self, mock_extract, mock_api, mock_channel, mock_stats, scraper):
        """Test successful competitor video fetching."""
        # Setup mocks
        mock_extract.return_value = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        mock_channel.return_value = MOCK_CHANNEL_RESPONSE["items"][0]
        mock_api.return_value = MOCK_PLAYLIST_RESPONSE
        mock_stats.return_value = {
            "test_video_1": {"viewCount": "50000", "likeCount": "1500", "commentCount": "200"},
            "test_video_2": {"viewCount": "30000", "likeCount": "900", "commentCount": "150"}
        }
        
        # Test the function
        result = scraper.fetch_competitor_videos("@testchannel", max_videos=5)
        
        # Assertions
        assert len(result) == 2
        assert result[0]['videoId'] == 'test_video_1'
        assert result[0]['videoTitle'] == 'Test Video 1'
        assert result[0]['views'] == 50000
        assert result[0]['channelTitle'] == 'Test Channel'
        
        # Check gap_detector compatibility fields
        assert 'impressions' in result[0]
        assert 'CTR' in result[0]
        assert 'averageViewDuration' in result[0]
        assert 'country' in result[0]
    
    def test_fetch_competitor_videos_no_api_key(self, scraper_no_key):
        """Test video fetching without API key."""
        with pytest.raises(ValueError, match="Could not extract channel ID"):
            scraper_no_key.fetch_competitor_videos("@testchannel")
    
    @patch('competitor_scraper.CompetitorScraper._extract_channel_id')
    def test_fetch_competitor_videos_invalid_channel(self, mock_extract, scraper):
        """Test video fetching with invalid channel."""
        mock_extract.return_value = None
        
        with pytest.raises(ValueError, match="Could not extract channel ID"):
            scraper.fetch_competitor_videos("invalid_channel")
    
    @patch('competitor_scraper.CompetitorScraper.fetch_competitor_videos')
    def test_save_competitor_data_success(self, mock_fetch, scraper):
        """Test successful competitor data saving."""
        # Mock video data
        mock_videos = [
            {
                'videoId': 'test1',
                'videoTitle': 'Test Video 1',
                'date': '2024-01-15',
                'views': 50000,
                'impressions': 500000,
                'CTR': 0.05,
                'averageViewDuration': 120,
                'country': 'Unknown',
                'channelId': 'UC-test',
                'channelTitle': 'Test Channel',
                'publishedAt': '2024-01-15T10:00:00Z',
                'description': 'Test description',
                'likes': 1500,
                'comments': 200
            }
        ]
        mock_fetch.return_value = mock_videos
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch DATA_DIR to use temp directory
            with patch('competitor_scraper.DATA_DIR', Path(temp_dir)):
                result_path = scraper.save_competitor_data("@testchannel", max_videos=5)
                
                # Check file was created
                assert os.path.exists(result_path)
                
                # Check CSV content
                df = pd.read_csv(result_path)
                assert len(df) == 1
                assert df.iloc[0]['videoTitle'] == 'Test Video 1'
                assert df.iloc[0]['views'] == 50000
    
    @patch('competitor_scraper.CompetitorScraper.fetch_competitor_videos')
    def test_save_competitor_data_no_videos(self, mock_fetch, scraper):
        """Test saving when no videos found."""
        mock_fetch.return_value = []
        
        with pytest.raises(ValueError, match="No videos found"):
            scraper.save_competitor_data("@testchannel")
    
    def test_rate_limiting(self, scraper):
        """Test rate limiting functionality."""
        # Set up rate limit scenario
        scraper.request_count = scraper.requests_per_minute
        scraper.last_request_time = 0  # Force rate limit
        
        with patch('time.sleep') as mock_sleep:
            with patch('time.time', return_value=30):  # 30 seconds after last request
                scraper._rate_limit()
                
                # Should sleep for remaining time
                mock_sleep.assert_called_once()
                assert scraper.request_count == 0
    
    @patch('requests.Session.get')
    def test_make_api_request_success(self, mock_get, scraper):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._make_api_request('channels', {'part': 'snippet'})
        
        assert result == {"items": []}
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_api_request_http_error(self, mock_get, scraper):
        """Test API request with HTTP error."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        result = scraper._make_api_request('channels', {'part': 'snippet'})
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_make_api_request_api_error(self, mock_get, scraper):
        """Test API request with API error response."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "API Error"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = scraper._make_api_request('channels', {'part': 'snippet'})
        
        assert result is None


class TestMultipleCompetitors:
    """Test multiple competitor processing."""
    
    @patch('competitor_scraper.CompetitorScraper.save_competitor_data')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_fetch_multiple_competitors_success(self, mock_sleep, mock_save):
        """Test fetching multiple competitors successfully."""
        mock_save.return_value = "/path/to/competitor.csv"
        
        competitors = ["@channel1", "@channel2"]
        results = fetch_multiple_competitors(competitors, max_videos=5)
        
        assert len(results) == 2
        assert results["@channel1"] == "/path/to/competitor.csv"
        assert results["@channel2"] == "/path/to/competitor.csv"
        
        # Verify save was called for each competitor
        assert mock_save.call_count == 2
    
    @patch('competitor_scraper.CompetitorScraper.save_competitor_data')
    @patch('time.sleep')
    def test_fetch_multiple_competitors_partial_failure(self, mock_sleep, mock_save):
        """Test fetching multiple competitors with some failures."""
        # First call succeeds, second fails
        mock_save.side_effect = ["/path/to/competitor1.csv", Exception("API Error")]
        
        competitors = ["@channel1", "@channel2"]
        results = fetch_multiple_competitors(competitors, max_videos=5)
        
        assert len(results) == 2
        assert results["@channel1"] == "/path/to/competitor1.csv"
        assert results["@channel2"] is None


class TestIntegration:
    """Integration tests for complete workflow."""
    
    @patch('competitor_scraper.CompetitorScraper._make_api_request')
    def test_complete_workflow(self, mock_api):
        """Test complete workflow from channel input to CSV output."""
        # Setup API responses in order
        mock_api.side_effect = [
            MOCK_SEARCH_RESPONSE,  # Channel search
            MOCK_CHANNEL_RESPONSE,  # Channel info
            MOCK_PLAYLIST_RESPONSE,  # Playlist items
            MOCK_VIDEO_STATS_RESPONSE  # Video statistics
        ]
        
        scraper = CompetitorScraper(api_key='test_key')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('competitor_scraper.DATA_DIR', Path(temp_dir)):
                # Test complete workflow
                csv_path = scraper.save_competitor_data("@testchannel", max_videos=5)
                
                # Verify file exists and has correct content
                assert os.path.exists(csv_path)
                
                df = pd.read_csv(csv_path)
                assert len(df) == 2
                assert 'videoId' in df.columns
                assert 'videoTitle' in df.columns
                assert 'views' in df.columns
                
                # Check gap_detector compatibility
                required_columns = ['videoId', 'videoTitle', 'date', 'views', 'impressions', 'CTR', 'averageViewDuration', 'country']
                for col in required_columns:
                    assert col in df.columns


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])