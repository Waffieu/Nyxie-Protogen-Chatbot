import logging
import datetime
import pytz
from typing import Dict, Any, Optional

import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache for last message times by user
user_last_message_times = {}

def get_current_time(timezone: str = None) -> datetime.datetime:
    """
    Get the current time in the specified timezone.
    
    Args:
        timezone: The timezone to use (default: config.DEFAULT_TIMEZONE)
        
    Returns:
        Current datetime in the specified timezone
    """
    if timezone is None:
        timezone = config.DEFAULT_TIMEZONE
        
    try:
        tz = pytz.timezone(timezone)
        return datetime.datetime.now(tz)
    except Exception as e:
        logger.error(f"Error getting time for timezone {timezone}: {e}")
        # Fall back to UTC
        return datetime.datetime.now(pytz.UTC)

def get_time_in_turkey() -> datetime.datetime:
    """
    Get the current time in Turkey.
    
    Returns:
        Current datetime in Turkey timezone
    """
    return get_current_time("Europe/Istanbul")

def get_time_period(dt: datetime.datetime) -> str:
    """
    Get the period of the day (morning, afternoon, evening, night) based on the hour.
    
    Args:
        dt: The datetime to check
        
    Returns:
        String representing the period of the day
    """
    hour = dt.hour
    
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"

def format_time_for_prompt(dt: datetime.datetime) -> str:
    """
    Format the time for inclusion in the prompt.
    
    Args:
        dt: The datetime to format
        
    Returns:
        Formatted time string
    """
    period = get_time_period(dt)
    weekday = dt.strftime("%A")
    date = dt.strftime("%Y-%m-%d")
    time = dt.strftime("%H:%M")
    
    return f"{weekday}, {date} at {time} ({period})"

def update_user_last_message_time(user_id: int) -> None:
    """
    Update the last message time for a user.
    
    Args:
        user_id: The user's ID
    """
    user_last_message_times[user_id] = datetime.datetime.now(pytz.UTC)

def get_time_since_last_message(user_id: int) -> Optional[datetime.timedelta]:
    """
    Get the time elapsed since the user's last message.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Timedelta representing elapsed time, or None if no previous message
    """
    if user_id not in user_last_message_times:
        return None
        
    now = datetime.datetime.now(pytz.UTC)
    last_time = user_last_message_times[user_id]
    return now - last_time

def format_time_since_last_message(delta: datetime.timedelta) -> str:
    """
    Format a timedelta into a human-readable string.
    
    Args:
        delta: The timedelta to format
        
    Returns:
        Human-readable string
    """
    if delta is None:
        return "first message"
        
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} seconds ago"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = total_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"

def get_time_awareness_context(user_id: int) -> Dict[str, Any]:
    """
    Get a dictionary with all time-related context for the user.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Dictionary with time context
    """
    turkey_time = get_time_in_turkey()
    time_period = get_time_period(turkey_time)
    formatted_time = format_time_for_prompt(turkey_time)
    
    # Get time since last message
    time_since_last = get_time_since_last_message(user_id)
    formatted_time_since = format_time_since_last_message(time_since_last)
    
    # Update last message time
    update_user_last_message_time(user_id)
    
    return {
        "current_time": turkey_time,
        "time_period": time_period,
        "formatted_time": formatted_time,
        "time_since_last_message": time_since_last,
        "formatted_time_since": formatted_time_since
    }
