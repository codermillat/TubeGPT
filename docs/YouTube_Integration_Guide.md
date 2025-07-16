# YouTube Data API v3 Integration Guide

## Overview

This guide explains how to set up and use the YouTube Data API v3 integration with your AI-powered SEO assistant. The integration provides comprehensive channel analytics, video performance insights, and AI-powered content strategy recommendations.

## Features

- **Channel Analytics**: Subscriber count, total views, video count, engagement metrics
- **Video Analysis**: Individual video performance, SEO optimization suggestions
- **Content Strategy**: AI-generated recommendations based on channel performance
- **Trend Analysis**: Search and analyze trending videos for content opportunities
- **Video Suggestions**: AI-powered video ideas based on your channel's context
- **Comments Analysis**: Extract insights from video comments
- **OAuth Authentication**: Secure access to your YouTube account with token refresh

## Prerequisites

- Python 3.9+
- Google Cloud Platform account
- YouTube channel (for testing and analysis)
- FastAPI application (already set up in this project)

## Setup Instructions

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3:
   - Navigate to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

### Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name, User support email, etc.)
   - Add your email to test users
4. Create OAuth 2.0 Client ID:
   - Application type: "Desktop application"
   - Name: "YouTube SEO Assistant"
   - Click "Create"
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in the `backend/` directory

### Step 3: Install Dependencies

The required dependencies are already included in `requirements_seo.txt`:

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### Step 4: Test the Integration

Run the test suite to verify everything is working:

```bash
# Run comprehensive tests
python yt_test.py

# Run quick authentication test
python yt_test.py --quick

# Run interactive test mode
python yt_test.py --interactive
```

## Usage

### Authentication

The first time you use the YouTube client, it will open a browser window for OAuth authentication:

1. Sign in with your Google account
2. Grant permissions to access your YouTube data
3. The client will save tokens for future use

### API Endpoints

#### 1. Channel Overview
Get comprehensive channel analytics with AI insights:

```bash
GET /youtube/overview
```

**Response:**
```json
{
  "channel_data": {
    "stats": {
      "channel_id": "UCxxxxx",
      "title": "Your Channel Name",
      "subscriber_count": 1000,
      "video_count": 50,
      "view_count": 100000
    },
    "analytics": {
      "recent_videos_count": 10,
      "avg_views_per_video": 2000,
      "engagement_rate": 5.2
    }
  },
  "ai_insights": "AI-generated recommendations...",
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Video Analysis
Analyze specific video performance:

```bash
GET /youtube/video/{video_id}/analyze
GET /youtube/video/analyze  # Analyzes latest video
```

#### 3. Content Strategy
Generate AI-powered content strategy:

```bash
GET /youtube/strategy?days_back=30
```

#### 4. Trend Analysis
Search and analyze trending videos:

```bash
GET /youtube/trends?query=python+tutorial&max_results=10
```

#### 5. Video Suggestions
Get AI-generated video ideas:

```bash
GET /youtube/suggestions?topic=python+programming
```

### Python Client Usage

```python
from backend.yt_client import YouTubeClient

# Initialize client
client = YouTubeClient()

# Authenticate
if client.authenticate():
    # Get channel stats
    stats = client.get_channel_stats()
    
    # Get latest videos
    videos = client.get_latest_videos(max_results=10)
    
    # Search videos
    results = client.search_videos("python tutorial", max_results=5)
    
    # Get video details
    video = client.get_video_by_id("your_video_id")
    
    # Get comments
    comments = client.get_video_comments("your_video_id", max_results=20)
    
    # Get comprehensive analytics
    analytics = client.get_channel_analytics(days_back=30)
```

## File Structure

```
backend/
├── yt_client.py          # Main YouTube client
├── credentials.json      # OAuth credentials (you need to create this)
├── token.json           # Access tokens (auto-generated)
├── ai_pipeline.py       # Updated with YouTube integration
└── api.py              # API with YouTube endpoints

yt_test.py               # Comprehensive test suite
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# YouTube API Configuration
YOUTUBE_API_KEY=your_api_key_here  # Optional, for API key authentication
YOUTUBE_CREDENTIALS_FILE=backend/credentials.json
YOUTUBE_TOKEN_FILE=backend/token.json

# Logging
LOG_LEVEL=INFO
```

### Scopes

The client uses these OAuth scopes:
- `https://www.googleapis.com/auth/youtube.readonly` - Read channel data
- `https://www.googleapis.com/auth/youtube.force-ssl` - Enhanced access

## Error Handling

The integration includes comprehensive error handling:

- **Authentication Errors**: Automatic token refresh
- **API Quota Limits**: Graceful degradation
- **Network Issues**: Retry logic with exponential backoff
- **Invalid Data**: Validation and sanitization

## Testing

### Unit Tests

Run the test suite to verify functionality:

```bash
# All tests
python yt_test.py

# Specific test categories
python -c "from yt_test import test_authentication; test_authentication()"
python -c "from yt_test import test_channel_stats; test_channel_stats()"
```

### Interactive Testing

Use the interactive test mode to manually test features:

```bash
python yt_test.py --interactive
```

This provides a menu-driven interface to test all YouTube features.

## Security Best Practices

1. **Credentials**: Never commit `credentials.json` to version control
2. **Tokens**: The `token.json` file contains sensitive access tokens
3. **Scopes**: Use minimal required scopes
4. **Rate Limiting**: Respect YouTube API quotas
5. **Data Storage**: All data is stored locally, no cloud storage

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check credentials.json exists and is valid
   - Verify OAuth consent screen is configured
   - Ensure YouTube Data API v3 is enabled

2. **API Quota Exceeded**
   - YouTube API has daily quotas
   - Implement caching for frequently accessed data
   - Consider using API keys for public data

3. **Invalid Video ID**
   - Ensure video IDs are valid YouTube video identifiers
   - Check if videos are public and accessible

4. **Import Errors**
   - Verify all dependencies are installed
   - Check Python path includes backend directory

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Quotas and Limits

- **Daily Quota**: 10,000 units per day (default)
- **Query Costs**:
  - Search: 100 units
  - Video details: 1 unit
  - Channel stats: 1 unit
  - Comments: 1 unit

## Advanced Usage

### Custom Authentication

```python
client = YouTubeClient(
    credentials_file='custom_credentials.json',
    token_file='custom_token.json'
)
```

### Batch Operations

```python
# Get multiple videos at once
video_ids = ['id1', 'id2', 'id3']
videos = client.get_videos_by_ids(video_ids)
```

### Custom Search Parameters

```python
# Search with date filtering
from datetime import datetime, timedelta
week_ago = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'

videos = client.search_videos(
    query="python tutorial",
    max_results=25,
    order="date",
    published_after=week_ago
)
```

## Integration with AI Pipeline

The YouTube client is fully integrated with the AI pipeline:

```python
# AI pipeline automatically uses YouTube data
from backend.ai_pipeline import seo_ai_pipeline

# Ask questions that trigger YouTube data fetching
response = seo_ai_pipeline.process_question(
    "How is my channel performing this month?"
)

# Get comprehensive channel insights
overview = seo_ai_pipeline.get_channel_overview()
```

## Performance Optimization

1. **Caching**: Implement Redis or local caching for frequently accessed data
2. **Batch Requests**: Use batch operations when possible
3. **Selective Fields**: Request only needed fields to reduce quota usage
4. **Pagination**: Handle large result sets efficiently

## Support

For issues and questions:
1. Check the test suite output for specific error messages
2. Review the logs for detailed error information
3. Consult the YouTube Data API documentation
4. Check Google Cloud Console for quota usage

## License

This integration is part of the AI SEO Assistant project and follows the same license terms. 