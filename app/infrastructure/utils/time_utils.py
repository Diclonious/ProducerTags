"""Centralized time utility for synchronized time across the application"""
from datetime import datetime, timezone, timedelta

# CEST timezone offset (UTC+2 in summer, UTC+1 in winter)
# For simplicity, using UTC+1 (CET) as default, adjust if needed for summer time
CEST_OFFSET = timedelta(hours=1)  # UTC+1 for CET (winter time)
# For summer time (CEST), use: timedelta(hours=2)


def get_current_time() -> datetime:
    """
    Get the current time in CEST (Central European Time).
    Returns timezone-naive datetime in CEST to match existing codebase.
    """
    # Get current UTC time
    utc_now = datetime.now(timezone.utc)
    # Convert to CEST (UTC+1 for CET, or UTC+2 for CEST in summer)
    cest_now = utc_now + CEST_OFFSET
    # Return as timezone-naive (removing timezone info to match existing codebase)
    return cest_now.replace(tzinfo=None)

