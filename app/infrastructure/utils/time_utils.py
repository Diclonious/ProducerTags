
from datetime import datetime, timezone, timedelta



CEST_OFFSET = timedelta(hours=1)



def get_current_time() -> datetime:
  

    utc_now = datetime.now(timezone.utc)

    cest_now = utc_now + CEST_OFFSET

    return cest_now.replace(tzinfo=None)

