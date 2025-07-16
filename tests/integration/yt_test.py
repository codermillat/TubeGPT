"""
YouTube Client Test Suite.
Independent tests for YouTube Data API v3 client functionality.
"""

import sys
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from yt_client import YouTubeClient, youtube_client


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, result: bool, details: str = ""):
    """Print test result with formatting."""
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")


def test_authentication():
    """Test YouTube API authentication."""
    print_section("Authentication Test")
    
    client = YouTubeClient()
    
    # Test authentication
    auth_success = client.authenticate()
    print_result("Authentication", auth_success, 
                f"Credentials valid: {client.credentials.valid if client.credentials else False}")
    
    # Test health check
    health = client.health_check()
    print_result("Health Check", health['status'] == 'healthy', 
                f"Status: {health['status']}")
    
    return auth_success


def test_channel_stats():
    """Test channel statistics retrieval."""
    print_section("Channel Statistics Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Channel Stats", False, "Authentication failed")
        return False
    
    try:
        # Get channel stats
        stats = client.get_channel_stats()
        
        success = bool(stats and 'channel_id' in stats)
        print_result("Get Channel Stats", success)
        
        if success:
            print(f"    Channel: {stats['title']}")
            print(f"    Subscribers: {stats['subscriber_count']:,}")
            print(f"    Total Views: {stats['view_count']:,}")
            print(f"    Video Count: {stats['video_count']:,}")
            print(f"    Published: {stats['published_at']}")
        
        return success
        
    except Exception as e:
        print_result("Channel Stats", False, f"Error: {e}")
        return False


def test_latest_videos():
    """Test latest videos retrieval."""
    print_section("Latest Videos Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Latest Videos", False, "Authentication failed")
        return False
    
    try:
        # Get latest 5 videos
        videos = client.get_latest_videos(max_results=5)
        
        success = bool(videos)
        print_result("Get Latest Videos", success, f"Found {len(videos)} videos")
        
        if success and videos:
            print("\n    Recent Videos:")
            for i, video in enumerate(videos[:3], 1):
                print(f"    {i}. {video['title']}")
                print(f"       Views: {video['view_count']:,} | Likes: {video['like_count']:,}")
                print(f"       Published: {video['published_at']}")
        
        return success
        
    except Exception as e:
        print_result("Latest Videos", False, f"Error: {e}")
        return False


def test_video_by_id():
    """Test individual video retrieval."""
    print_section("Video By ID Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Video By ID", False, "Authentication failed")
        return False
    
    try:
        # First get a video ID from latest videos
        videos = client.get_latest_videos(max_results=1)
        
        if not videos:
            print_result("Video By ID", False, "No videos found to test with")
            return False
        
        video_id = videos[0]['video_id']
        
        # Get detailed video info
        video = client.get_video_by_id(video_id)
        
        success = bool(video and 'video_id' in video)
        print_result("Get Video By ID", success)
        
        if success:
            print(f"    Title: {video['title']}")
            print(f"    Description: {video['description'][:100]}...")
            print(f"    Tags: {', '.join(video['tags'][:5])}")
            print(f"    Duration: {video['duration']}")
            print(f"    Views: {video['view_count']:,}")
            print(f"    Likes: {video['like_count']:,}")
            print(f"    Comments: {video['comment_count']:,}")
        
        return success
        
    except Exception as e:
        print_result("Video By ID", False, f"Error: {e}")
        return False


def test_search_videos():
    """Test video search functionality."""
    print_section("Video Search Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Video Search", False, "Authentication failed")
        return False
    
    try:
        # Search for videos
        search_query = "python tutorial"
        videos = client.search_videos(search_query, max_results=5)
        
        success = bool(videos)
        print_result("Search Videos", success, f"Found {len(videos)} videos for '{search_query}'")
        
        if success and videos:
            print("\n    Search Results:")
            for i, video in enumerate(videos[:3], 1):
                print(f"    {i}. {video['title']}")
                print(f"       Channel: {video['channel_title']}")
                print(f"       Views: {video['view_count']:,}")
                print(f"       Search Rank: {video['search_rank']}")
        
        return success
        
    except Exception as e:
        print_result("Video Search", False, f"Error: {e}")
        return False


def test_video_comments():
    """Test video comments retrieval."""
    print_section("Video Comments Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Video Comments", False, "Authentication failed")
        return False
    
    try:
        # Get a video ID from latest videos
        videos = client.get_latest_videos(max_results=1)
        
        if not videos:
            print_result("Video Comments", False, "No videos found to test with")
            return False
        
        video_id = videos[0]['video_id']
        
        # Get comments
        comments = client.get_video_comments(video_id, max_results=5)
        
        success = True  # Comments might be empty, which is valid
        print_result("Get Video Comments", success, f"Found {len(comments)} comments")
        
        if comments:
            print("\n    Recent Comments:")
            for i, comment in enumerate(comments[:3], 1):
                print(f"    {i}. {comment['author']}: {comment['text'][:50]}...")
                print(f"       Likes: {comment['like_count']} | Replies: {comment['reply_count']}")
        else:
            print("    No comments found (may be disabled)")
        
        return success
        
    except Exception as e:
        print_result("Video Comments", False, f"Error: {e}")
        return False


def test_channel_analytics():
    """Test comprehensive channel analytics."""
    print_section("Channel Analytics Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Channel Analytics", False, "Authentication failed")
        return False
    
    try:
        # Get channel analytics
        analytics = client.get_channel_analytics(days_back=30)
        
        success = bool(analytics and 'channel_info' in analytics)
        print_result("Get Channel Analytics", success)
        
        if success:
            channel_info = analytics['channel_info']
            stats = analytics['analytics']
            
            print(f"\n    Channel: {channel_info['title']}")
            print(f"    Analysis Period: {analytics['period_days']} days")
            print(f"    Recent Videos: {analytics['recent_videos_count']}")
            print(f"    Total Views: {stats['total_views']:,}")
            print(f"    Total Likes: {stats['total_likes']:,}")
            print(f"    Avg Views/Video: {stats['avg_views_per_video']:,}")
            print(f"    Engagement Rate: {stats['engagement_rate']}%")
            
            if analytics['top_performing_video']:
                top_video = analytics['top_performing_video']
                print(f"    Top Video: {top_video['title']}")
                print(f"    Top Video Views: {top_video['view_count']:,}")
        
        return success
        
    except Exception as e:
        print_result("Channel Analytics", False, f"Error: {e}")
        return False


def test_error_handling():
    """Test error handling and edge cases."""
    print_section("Error Handling Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print_result("Error Handling", False, "Authentication failed")
        return False
    
    try:
        # Test invalid video ID
        invalid_video = client.get_video_by_id("invalid_video_id")
        test1 = invalid_video == {}
        print_result("Invalid Video ID", test1, "Returns empty dict for invalid ID")
        
        # Test empty search
        empty_search = client.search_videos("", max_results=1)
        test2 = isinstance(empty_search, list)
        print_result("Empty Search Query", test2, "Handles empty search gracefully")
        
        # Test non-existent channel
        invalid_channel = client.get_channel_stats("invalid_channel_id")
        test3 = invalid_channel == {}
        print_result("Invalid Channel ID", test3, "Returns empty dict for invalid channel")
        
        return test1 and test2 and test3
        
    except Exception as e:
        print_result("Error Handling", False, f"Error: {e}")
        return False


def test_global_instance():
    """Test the global YouTube client instance."""
    print_section("Global Instance Test")
    
    try:
        # Test global instance
        auth_success = youtube_client.authenticate()
        print_result("Global Instance Auth", auth_success)
        
        if auth_success:
            health = youtube_client.health_check()
            health_success = health['status'] == 'healthy'
            print_result("Global Instance Health", health_success, f"Status: {health['status']}")
            
            return health_success
        
        return False
        
    except Exception as e:
        print_result("Global Instance", False, f"Error: {e}")
        return False


def run_comprehensive_test():
    """Run all YouTube client tests."""
    print_section("YouTube Client Comprehensive Test Suite")
    print("Testing YouTube Data API v3 client functionality...")
    
    # Track test results
    test_results = {}
    
    # Run all tests
    test_results['authentication'] = test_authentication()
    test_results['channel_stats'] = test_channel_stats()
    test_results['latest_videos'] = test_latest_videos()
    test_results['video_by_id'] = test_video_by_id()
    test_results['search_videos'] = test_search_videos()
    test_results['video_comments'] = test_video_comments()
    test_results['channel_analytics'] = test_channel_analytics()
    test_results['error_handling'] = test_error_handling()
    test_results['global_instance'] = test_global_instance()
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! YouTube client is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
        # Show failed tests
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")
    
    return passed == total


def interactive_test():
    """Interactive test mode for manual testing."""
    print_section("Interactive YouTube Client Test")
    
    client = YouTubeClient()
    if not client.authenticate():
        print("❌ Authentication failed!")
        return
    
    print("✅ Authentication successful!")
    
    while True:
        print("\nAvailable commands:")
        print("1. Channel stats")
        print("2. Latest videos")
        print("3. Search videos")
        print("4. Video details")
        print("5. Video comments")
        print("6. Channel analytics")
        print("7. Health check")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            stats = client.get_channel_stats()
            print(f"\nChannel Statistics:")
            print(json.dumps(stats, indent=2))
        
        elif choice == '2':
            count = int(input("Number of videos to fetch (default 5): ") or "5")
            videos = client.get_latest_videos(max_results=count)
            print(f"\nLatest {len(videos)} Videos:")
            for i, video in enumerate(videos, 1):
                print(f"{i}. {video['title']} ({video['view_count']:,} views)")
        
        elif choice == '3':
            query = input("Search query: ").strip()
            if query:
                videos = client.search_videos(query, max_results=5)
                print(f"\nSearch Results for '{query}':")
                for i, video in enumerate(videos, 1):
                    print(f"{i}. {video['title']} - {video['channel_title']}")
        
        elif choice == '4':
            video_id = input("Video ID: ").strip()
            if video_id:
                video = client.get_video_by_id(video_id)
                print(f"\nVideo Details:")
                print(json.dumps(video, indent=2))
        
        elif choice == '5':
            video_id = input("Video ID: ").strip()
            if video_id:
                comments = client.get_video_comments(video_id, max_results=5)
                print(f"\nComments ({len(comments)} found):")
                for i, comment in enumerate(comments, 1):
                    print(f"{i}. {comment['author']}: {comment['text'][:100]}...")
        
        elif choice == '6':
            days = int(input("Days back to analyze (default 30): ") or "30")
            analytics = client.get_channel_analytics(days_back=days)
            print(f"\nChannel Analytics:")
            print(json.dumps(analytics, indent=2))
        
        elif choice == '7':
            health = client.health_check()
            print(f"\nHealth Check:")
            print(json.dumps(health, indent=2))
        
        elif choice == '8':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Client Test Suite")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run interactive test mode")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick authentication test only")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_test()
    elif args.quick:
        test_authentication()
    else:
        run_comprehensive_test() 