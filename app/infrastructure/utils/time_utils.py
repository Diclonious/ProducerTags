"""Centralized time utility for synchronized time across the application"""
from datetime import datetime, timezone, timedelta



CEST_OFFSET = timedelta(hours=1)



def get_current_time() -> datetime:
    """
    Get the current time in CEST (Central European Time).
    Returns timezone-naive datetime in CEST to match existing codebase.
    """

    utc_now = datetime.now(timezone.utc)

    cest_now = utc_now + CEST_OFFSET

    return cest_now.replace(tzinfo=None)

