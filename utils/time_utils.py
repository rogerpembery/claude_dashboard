from datetime import datetime

def get_relative_time(timestamp):
    try:
        dt = datetime.fromtimestamp(timestamp)
        diff = datetime.now() - dt
        if diff.days > 7:
            return dt.strftime("%b %d")
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "now"
    except:
        return "unknown"