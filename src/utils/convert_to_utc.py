
from datetime import datetime, timezone
import re
import pytz

def parse_time_string(time_str):
    """
    Parse time into a standardized format (e.g. 12:01 AM)
    """
    if not time_str:
        return None
        
    time_str = time_str.strip().lower()
    
    # sometimes written as p.m.
    time_str = time_str.replace("p.m.", "pm").replace("a.m.", "am")
    
    # extract hours, minutes, and AM/PM
    time_pattern = re.compile(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?')
    match = time_pattern.search(time_str)
    
    if not match:
        return None
        
    hours = match.group(1)
    minutes = match.group(2) or "00"
    
    # default to pm if not specified
    am_pm = match.group(3) or "pm" 
    
    return f"{hours}:{minutes} {am_pm.upper()}"

def convert_to_utc(date_str, time_str, eastern_tz=pytz.timezone('US/Eastern')):
    """
    Convert date and time strings to UTC datetime. 
    e.g. date_str: "Aug 31 (Sat) 2024"
         time_str: "12:00 PM"
    """
    if not date_str:
        return None
        
    try:
        # remove day of week in parentheses
        date_str = re.sub(r'\([^)]*\)', '', date_str).strip()
        
        standardized_time = parse_time_string(time_str)
        
        if standardized_time:
            datetime_str = f"{date_str} {standardized_time}"

            # sometimes written in different formats
            for fmt in ["%b %d %Y %I:%M %p", "%B %d %Y %I:%M %p", "%b. %d %Y %I:%M %p"]:
                try:
                    local_dt = eastern_tz.localize(datetime.strptime(datetime_str, fmt))
                    return local_dt.astimezone(timezone.utc)
                except ValueError:
                    continue
        
        # default to midnight
        for fmt in ["%b %d %Y", "%B %d %Y", "%b. %d %Y"]:
            try:
                local_dt = eastern_tz.localize(datetime.strptime(date_str, fmt).replace(hour=0, minute=0))
                return local_dt.astimezone(timezone.utc)
            except ValueError:
                continue
                
    except Exception as e:
        print(f"Error converting date/time to UTC: {e} for date={date_str}, time={time_str}")
    
    return None