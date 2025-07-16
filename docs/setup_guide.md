# YouTube Analytics Fetcher Setup Guide

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with YouTube APIs enabled
2. **Python 3.7+**: Make sure you have Python 3.7 or later installed
3. **YouTube Channel**: You need a YouTube channel to fetch analytics from

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - YouTube Data API v3
   - YouTube Analytics API

### 3. Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Download the credentials JSON file
5. Save it as `credentials.json` in the project directory

### 4. First Run

```bash
python yt_fetch.py
```

On first run, it will:
- Open a browser window for OAuth authentication
- Ask you to sign in to your Google account
- Request permission to access your YouTube data
- Save the authentication token for future use

### 5. Verify Output

Check the generated `yt_analytics.csv` file for your YouTube data.

## Usage Examples

### Basic Usage

```python
from yt_fetch import YouTubeAnalyticsFetcher

# Initialize and authenticate
fetcher = YouTubeAnalyticsFetcher()
fetcher.authenticate()

# Fetch data for last 30 days
fetcher.fetch_and_save_data(days_back=30, max_results=50)
```

### Custom Configuration

```python
# Fetch data for last 7 days, max 100 videos
fetcher.fetch_and_save_data(
    days_back=7,
    max_results=100,
    output_file='weekly_analytics.csv'
)
```

## Scheduling

### Daily Run (Linux/Mac)

Add to crontab:
```bash
0 9 * * * /usr/bin/python3 /path/to/run_daily.py
```

### Weekly Run (Linux/Mac)

Add to crontab:
```bash
0 9 * * 1 /usr/bin/python3 /path/to/run_weekly.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily/weekly)
4. Set action to start `python.exe` with arguments pointing to your script

## Output Format

The CSV file contains the following columns:
- `videoId`: YouTube video ID
- `videoTitle`: Video title
- `date`: Publication date (YYYY-MM-DD)
- `views`: Total view count
- `impressions`: Total impressions
- `CTR`: Click-through rate (decimal)
- `averageViewDuration`: Average view duration in seconds
- `country`: Top country for the video

## Troubleshooting

### Authentication Issues

1. Delete `token.json` and re-authenticate
2. Check that your Google account has access to the YouTube channel
3. Ensure APIs are enabled in Google Cloud Console

### API Quotas

- YouTube Data API has daily quotas
- Analytics API has rate limits
- The script includes error handling for quota issues

### Missing Data

- Analytics data may not be available for very recent videos
- Some metrics might be 0 for newer videos
- Country data aggregates to the top country by impressions

## File Structure

```
├── yt_fetch.py              # Main module
├── config.py               # Configuration settings
├── run_daily.py            # Daily runner script
├── run_weekly.py           # Weekly runner script
├── requirements.txt        # Python dependencies
├── credentials.json        # OAuth credentials (you provide)
├── token.json             # Generated auth token
└── yt_analytics.csv       # Output data file
```