"""
Configuration settings for YouTube Analytics Fetcher.
Modify these values according to your needs.
"""

# Default settings
DEFAULT_DAYS_BACK = 30
DEFAULT_MAX_RESULTS = 50
DEFAULT_OUTPUT_FILE = 'yt_analytics.csv'

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# API rate limiting (requests per minute)
API_RATE_LIMIT = 100

# CSV column headers
CSV_COLUMNS = [
    'videoId',
    'videoTitle', 
    'date',
    'views',
    'impressions',
    'CTR',
    'averageViewDuration',
    'country'
]