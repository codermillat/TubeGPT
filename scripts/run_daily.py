#!/usr/bin/env python3
"""
Daily runner script for YouTube Analytics Fetcher.
This script can be scheduled to run daily via cron or task scheduler.
"""

import sys
import os
from datetime import datetime
from yt_fetch import YouTubeAnalyticsFetcher
import logging

# Set up logging for scheduled runs
log_filename = f"yt_fetch_daily_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_daily_fetch():
    """Run daily YouTube analytics fetch."""
    try:
        logger.info("Starting daily YouTube analytics fetch")
        
        # Initialize fetcher
        fetcher = YouTubeAnalyticsFetcher()
        
        # Authenticate (will use existing token if valid)
        fetcher.authenticate()
        
        # Fetch data for the last 7 days (adjust as needed)
        output_file = f"yt_analytics_daily_{datetime.now().strftime('%Y%m%d')}.csv"
        
        fetcher.fetch_and_save_data(
            days_back=7,
            max_results=100,
            output_file=output_file
        )
        
        logger.info(f"Daily fetch completed successfully. Output: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Daily fetch failed: {e}")
        return False

if __name__ == "__main__":
    success = run_daily_fetch()
    sys.exit(0 if success else 1)