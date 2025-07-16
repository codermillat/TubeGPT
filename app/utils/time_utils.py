"""
Time utilities for YouTube SEO Assistant.

Cursor Rules:
- Use environment variables for configuration
- Add descriptive docstrings
- Implement proper error handling
- Follow consistent naming conventions
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Tuple


class TimeTracker:
    """Utility class for time tracking and timestamp generation."""
    
    def __init__(self):
        """Initialize time tracker."""
        self.start_time = time.time()
    
    def get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp string
        """
        return datetime.now().isoformat().replace(':', '-').replace('.', '-')
    
    def get_detailed_timestamp(self) -> str:
        """
        Get detailed timestamp with microseconds.
        
        Returns:
            Detailed timestamp string
        """
        return datetime.now().isoformat()
    
    def get_human_readable_time(self) -> str:
        """
        Get human-readable time format.
        
        Returns:
            Human-readable time string
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp as string.
        
        Returns:
            Current timestamp string
        """
        return str(int(time.time()))
    
    def generate_filename(self, prefix: str = "file", extension: str = "json") -> str:
        """
        Generate filename with timestamp.
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            Generated filename
        """
        timestamp = self.get_timestamp()
        return f"{timestamp}_{prefix}.{extension}"
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string to datetime object.
        
        Args:
            timestamp_str: Timestamp string to parse
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # Try ISO format first
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Try timestamp format
            return datetime.fromtimestamp(float(timestamp_str))
            
        except (ValueError, TypeError):
            return None
    
    def get_date_range(self, days_back: int) -> Tuple[datetime, datetime]:
        """
        Get date range for the last N days.
        
        Args:
            days_back: Number of days to go back
            
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return start_date, end_date
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since initialization.
        
        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time
    
    def format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Human-readable duration string
        """
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def is_within_time_range(
        self,
        timestamp: datetime,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if timestamp is within time range.
        
        Args:
            timestamp: Timestamp to check
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            True if timestamp is within range, False otherwise
        """
        return start_time <= timestamp <= end_time
    
    def get_time_ago(self, timestamp: datetime) -> str:
        """
        Get human-readable time ago string.
        
        Args:
            timestamp: Timestamp to compare
            
        Returns:
            Human-readable time ago string
        """
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    
    def get_next_occurrence(self, hour: int, minute: int = 0) -> datetime:
        """
        Get next occurrence of specified time.
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
            
        Returns:
            Next occurrence datetime
        """
        now = datetime.now()
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If target time has passed today, move to tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)
        
        return target_time
    
    def get_business_hours_remaining(self, start_hour: int = 9, end_hour: int = 17) -> float:
        """
        Get remaining business hours for today.
        
        Args:
            start_hour: Business start hour (default: 9 AM)
            end_hour: Business end hour (default: 5 PM)
            
        Returns:
            Remaining business hours (0 if outside business hours)
        """
        now = datetime.now()
        
        # Check if it's a weekday
        if now.weekday() > 4:  # Saturday = 5, Sunday = 6
            return 0.0
        
        # Check if within business hours
        if now.hour < start_hour or now.hour >= end_hour:
            return 0.0
        
        # Calculate remaining hours
        end_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        remaining_seconds = (end_time - now).total_seconds()
        
        return max(0.0, remaining_seconds / 3600)
    
    def get_timezone_offset(self) -> str:
        """
        Get current timezone offset.
        
        Returns:
            Timezone offset string (e.g., '+05:30')
        """
        # Get timezone offset
        offset = datetime.now().astimezone().utcoffset()
        
        if offset is None:
            return "+00:00"
        
        # Convert to hours and minutes
        total_seconds = int(offset.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        # Format as +/-HH:MM
        sign = "+" if total_seconds >= 0 else "-"
        return f"{sign}{abs(hours):02d}:{abs(minutes):02d}"
    
    def sleep_until(self, target_time: datetime) -> None:
        """
        Sleep until specified time.
        
        Args:
            target_time: Target time to sleep until
        """
        now = datetime.now()
        
        if target_time <= now:
            return
        
        sleep_duration = (target_time - now).total_seconds()
        time.sleep(sleep_duration) 