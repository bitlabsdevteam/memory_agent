"""Time tool for getting current time information."""

from datetime import datetime
import pytz
from typing import Optional

def time_tool(timezone: Optional[str] = None) -> str:
    """
    Get current time, optionally for a specific timezone.
    
    Args:
        timezone (str, optional): Timezone name (e.g., 'US/Eastern', 'Europe/London')
        
    Returns:
        str: Current time information
    """
    try:
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                current_time = datetime.now(tz)
                return f"Current time in {timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            except pytz.exceptions.UnknownTimeZoneError:
                # Fallback to UTC if timezone is invalid
                current_time = datetime.now(pytz.UTC)
                return f"Invalid timezone '{timezone}'. Current UTC time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        else:
            # Default to local time
            current_time = datetime.now()
            return f"Current local time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Sorry, I couldn't get the current time. Error: {str(e)}"