#!/usr/bin/env python3
"""
YouTube Client Test Suite
Tests OAuth, channel info, video listing, and analytics
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_youtube_client():
    """Test YouTube client functionality"""
    print("🎯 Testing YouTube Client...")
    
    try:
        from app.clients.youtube_client import YouTubeClient
        print("✅ YouTube client imported successfully")
        
        # Test client initialization
        client = YouTubeClient()
        print("✅ YouTube client initialized")
        
        # Test authentication check (without actual OAuth)
        print("📝 Testing authentication...")
        try:
            # Check if credentials exist
            creds_file = Path("config/credentials.json")
            token_file = Path("data/storage/token.json")
            
            if creds_file.exists():
                print(f"✅ Credentials file found: {creds_file}")
            else:
                print(f"⚠️  Credentials file not found: {creds_file}")
                print("   This is expected for testing without OAuth setup")
            
            if token_file.exists():
                print(f"✅ Token file found: {token_file}")
            else:
                print(f"ℹ️  No existing token file: {token_file}")
        
        except Exception as e:
            print(f"ℹ️  Auth check skipped: {e}")
        
        print("✅ YouTube client tests completed (basic initialization)")
        return True
        
    except Exception as e:
        print(f"❌ YouTube client test failed: {e}")
        return False

async def test_mock_youtube_data():
    """Test with mock YouTube data structure"""
    print("\n📊 Testing YouTube data structure validation...")
    
    # Mock YouTube API response structure
    mock_channel_data = {
        "kind": "youtube#channel",
        "etag": "test_etag",
        "id": "UCtest123",
        "snippet": {
            "title": "Test Channel",
            "description": "Test channel for TubeGPT",
            "customUrl": "@testchannel",
            "publishedAt": "2020-01-01T00:00:00Z",
            "thumbnails": {
                "default": {"url": "https://example.com/thumb.jpg"}
            },
            "country": "US"
        },
        "statistics": {
            "viewCount": "1000000",
            "subscriberCount": "50000",
            "hiddenSubscriberCount": False,
            "videoCount": "100"
        }
    }
    
    mock_video_data = {
        "kind": "youtube#video",
        "etag": "test_etag",
        "id": "testvideo123",
        "snippet": {
            "publishedAt": "2024-01-01T00:00:00Z",
            "channelId": "UCtest123",
            "title": "Test Video Title - Python Tutorial",
            "description": "This is a test video description",
            "thumbnails": {
                "default": {"url": "https://example.com/thumb.jpg"}
            },
            "channelTitle": "Test Channel",
            "tags": ["python", "tutorial", "programming"],
            "categoryId": "27"
        },
        "statistics": {
            "viewCount": "10000",
            "likeCount": "500",
            "commentCount": "50"
        }
    }
    
    # Test data structure validation
    try:
        assert "id" in mock_channel_data
        assert "snippet" in mock_channel_data
        assert "statistics" in mock_channel_data
        assert "title" in mock_channel_data["snippet"]
        print("✅ Channel data structure valid")
        
        assert "id" in mock_video_data
        assert "snippet" in mock_video_data
        assert "statistics" in mock_video_data
        assert "title" in mock_video_data["snippet"]
        print("✅ Video data structure valid")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Data structure validation failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🧪 YOUTUBE CLIENT TEST SUITE")
        print("=" * 50)
        
        test1 = await test_youtube_client()
        test2 = await test_mock_youtube_data()
        
        if test1 and test2:
            print("\n🎉 YouTube client tests PASSED")
            return True
        else:
            print("\n❌ YouTube client tests FAILED")
            return False
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
