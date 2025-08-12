"""
Time utility functions.
"""
from datetime import datetime


def debug_log(message):
    """Debug logging function"""
    print(f"[DEBUG] {message}")


def get_relative_time(timestamp):
    """
    Convert timestamp to relative time string.
    
    Args:
        timestamp (float): Unix timestamp
        
    Returns:
        str: Human-readable relative time string
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 7:
            return dt.strftime("%b %d")
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except Exception as e:
        debug_log(f"Error formatting time: {e}")
        return "Unknown"