import os

# JWT 
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

# Base URL
BASE_URL = "https://cornellbigred.com"

# US state names and abbreviations as the calendar feed writes them, mapped to a
# canonical two-letter form. The feed is inconsistent about this: Ithaca appears
# as both "Ithaca, N.Y." and "Ithaca, NY", so without normalizing, the same
# venue produces two different games.
STATE_ABBREVIATIONS = {
    # Associated Press style, which is what the feed writes ("Conn.", "Calif.").
    "ALA": "AL", "ARIZ": "AZ", "ARK": "AR", "CALIF": "CA", "CAL": "CA",
    "COLO": "CO", "CONN": "CT", "DEL": "DE", "FLA": "FL", "GA": "GA",
    "ILL": "IL", "IND": "IN", "KAN": "KS", "KANS": "KS", "KY": "KY",
    "LA": "LA", "MASS": "MA", "MD": "MD", "MICH": "MI", "MINN": "MN",
    "MISS": "MS", "MO": "MO", "MONT": "MT", "NEB": "NE", "NEBR": "NE",
    "NEV": "NV", "OKLA": "OK", "ORE": "OR", "OREG": "OR", "PA": "PA",
    "TENN": "TN", "TEX": "TX", "VT": "VT", "VA": "VA", "WASH": "WA",
    "WIS": "WI", "WISC": "WI", "WYO": "WY",
    # States AP never abbreviates, so the feed spells them out in full. Without
    # these they are left as-is and the same venue reads as two places.
    "ALASKA": "AK", "HAWAII": "HI", "IDAHO": "ID", "IOWA": "IA",
    "MAINE": "ME", "OHIO": "OH", "TEXAS": "TX", "UTAH": "UT",
    # Multi-word states, which lose their spaces and periods before lookup.
    "WVA": "WV", "WVIRGINIA": "WV", "WESTVIRGINIA": "WV",
    "NMEX": "NM", "NEWMEXICO": "NM", "NEWYORK": "NY", "NEWJERSEY": "NJ",
    "NEWHAMPSHIRE": "NH", "RHODEISLAND": "RI", "NORTHCAROLINA": "NC",
    "SOUTHCAROLINA": "SC", "NORTHDAKOTA": "ND", "SOUTHDAKOTA": "SD",
    "NDAK": "ND", "SDAK": "SD", "DISTRICTOFCOLUMBIA": "DC",
}

CALENDAR_URL = f"https://cornellbigred.com/services/responsive-calendar.ashx?type=events&sport=0&location=all"

# The prefix for the live games
LIVE_PREFIX = "https://cornellbigred.com/sports/calendar?vtype=list/"

# HTML Tags
TAG_TABLE = 'table'
TAG_SECTION = 'section'
TAG_TBODY = 'tbody'
TAG_TR = 'tr'
TAG_TD = 'td'
TAG_TH = 'th'
TAG_SPAN = 'span'
TAG_IMG = 'img'

# HTML Classes
CLASS_SIDEARM_TABLE = 'sidearm-table'
CLASS_SCORING_SUMMARY = 'scoring-summary'
CLASS_OVERALL_STATS = 'overall-stats'
CLASS_BOX_SCORE = 'box-score'

# HTML Attributes
ATTR_ARIA_LABEL = 'aria-label'
ATTR_ALT = 'alt'

# HTML IDs for Sections
ID_BOX_SCORE = 'box-score'

# Labels
LABEL_SCORING_SUMMARY = 'Scoring Summary'

# The dictionary mapping sports urls to gender
SPORT_URLS = {
    "baseball": {"sport": "Baseball", "gender": "Mens"},
    "mens-basketball": {"sport": "Basketball", "gender": "Mens"},
    "mens-cross-country": {"sport": "Cross Country", "gender": "Mens"},
    "football": {"sport": "Football", "gender": "Mens"},
    "mens-golf": {"sport": "Golf", "gender": "Mens"},
    "mens-ice-hockey": {"sport": "Ice Hockey", "gender": "Mens"},
    "mens-lacrosse": {"sport": "Lacrosse", "gender": "Mens"},
    "mens-polo": {"sport": "Polo", "gender": "Mens"},
    "rowing": {"sport": "Rowing - Heavyweight", "gender": "Mens"},
    "mens-rowing": {"sport": "Rowing - Lightweight", "gender": "Mens"},
    "mens-soccer": {"sport": "Soccer", "gender": "Mens"},
    "sprint-football": {"sport": "Sprint Football", "gender": "Mens"},
    "mens-squash": {"sport": "Squash", "gender": "Mens"},
    "mens-swimming-and-diving": {"sport": "Swimming & Diving", "gender": "Mens"},
    "mens-tennis": {"sport": "Tennis", "gender": "Mens"},
    "mens-track-and-field": {"sport": "Track & Field", "gender": "Mens"},
    "wrestling": {"sport": "Wrestling", "gender": "Mens"},
    "womens-basketball": {"sport": "Basketball", "gender": "Womens"},
    "womens-cross-country": {"sport": "Cross Country", "gender": "Womens"},
    "equestrian": {"sport": "Equestrian", "gender": "Womens"},
    "fencing": {"sport": "Fencing", "gender": "Womens"},
    "field-hockey": {"sport": "Field Hockey", "gender": "Womens"},
    "womens-gymnastics": {"sport": "Gymnastics", "gender": "Womens"},
    "womens-ice-hockey": {"sport": "Ice Hockey", "gender": "Womens"},
    "womens-lacrosse": {"sport": "Lacrosse", "gender": "Womens"},
    "womens-polo": {"sport": "Polo", "gender": "Womens"},
    "womens-rowing": {"sport": "Rowing ", "gender": "Womens"},
    "womens-sailing": {"sport": "Sailing", "gender": "Womens"},
    "womens-soccer": {"sport": "Soccer", "gender": "Womens"},
    "softball": {"sport": "Softball", "gender": "Womens"},
    "womens-squash": {"sport": "Squash", "gender": "Womens"},
    "womens-swimming-and-diving": {"sport": "Swimming & Diving", "gender": "Womens"},
    "womens-tennis": {"sport": "Tennis", "gender": "Womens"},
    "womens-track-and-field": {"sport": "Track & Field", "gender": "Womens"},
    "womens-volleyball": {"sport": "Volleyball", "gender": "Womens"},
}

# Maps Sidearm's global sport shortname (the "global_sport_shortname" on a
# calendar event, also the sport segment of a livestats URL) to our sport/gender.
# Sport names must match SPORT_URLS exactly, since that is what gets written to
# the database and what live games are looked up by.
SIDEARM_SPORTS = {
    "baseball": {"sport": "Baseball", "gender": "Mens"},
    "equest": {"sport": "Equestrian", "gender": "Womens"},
    "fencing": {"sport": "Fencing", "gender": "Womens"},
    "fhockey": {"sport": "Field Hockey", "gender": "Womens"},
    "football": {"sport": "Football", "gender": "Mens"},
    "mbball": {"sport": "Basketball", "gender": "Mens"},
    "mcross": {"sport": "Cross Country", "gender": "Mens"},
    "mgolf": {"sport": "Golf", "gender": "Mens"},
    "mhockey": {"sport": "Ice Hockey", "gender": "Mens"},
    "mlax": {"sport": "Lacrosse", "gender": "Mens"},
    "mpolo": {"sport": "Polo", "gender": "Mens"},
    "mrow": {"sport": "Rowing - Lightweight", "gender": "Mens"},
    "msoc": {"sport": "Soccer", "gender": "Mens"},
    "msquash": {"sport": "Squash", "gender": "Mens"},
    "mswim": {"sport": "Swimming & Diving", "gender": "Mens"},
    "mten": {"sport": "Tennis", "gender": "Mens"},
    "mtrack": {"sport": "Track & Field", "gender": "Mens"},
    "row": {"sport": "Rowing - Heavyweight", "gender": "Mens"},
    "sfootball": {"sport": "Sprint Football", "gender": "Mens"},
    "softball": {"sport": "Softball", "gender": "Womens"},
    "wbball": {"sport": "Basketball", "gender": "Womens"},
    "wcross": {"sport": "Cross Country", "gender": "Womens"},
    "wgym": {"sport": "Gymnastics", "gender": "Womens"},
    "whockey": {"sport": "Ice Hockey", "gender": "Womens"},
    "wlax": {"sport": "Lacrosse", "gender": "Womens"},
    "wpolo": {"sport": "Polo", "gender": "Womens"},
    "wrestling": {"sport": "Wrestling", "gender": "Mens"},
    # trailing space matches SPORT_URLS["womens-rowing"]
    "wrow": {"sport": "Rowing ", "gender": "Womens"},
    "wsail": {"sport": "Sailing", "gender": "Womens"},
    "wsoc": {"sport": "Soccer", "gender": "Womens"},
    "wsquash": {"sport": "Squash", "gender": "Womens"},
    "wswim": {"sport": "Swimming & Diving", "gender": "Womens"},
    "wten": {"sport": "Tennis", "gender": "Womens"},
    "wtrack": {"sport": "Track & Field", "gender": "Womens"},
    "wvball": {"sport": "Volleyball", "gender": "Womens"},
}

# Cornell Sports YouTube Channel ID
CHANNEL_ID = "UClSQOi2gnn9bi7mcgQrAVKA"

# The maximum number of videos to retrieve
VIDEO_LIMIT = 20

ARTICLE_IMG_TAG = ".dom-art-container img"

# Restored: still used by the recap and URL-safety helpers.
ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

ALLOWED_URL_HOSTS = frozenset({
    "cornellbigred.com",
    "dxbhsrqyrr690.cloudfront.net",
})

HTTP_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CornellSportsScraper/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SIDEARM_STORY_HEADLINE = "h1.sidearm-story-template-headline"

SIDEARM_STORY_IMAGE = ".sidearm-story-template-media img"

SIDEARM_STORY_PUBLISHED_TIME = "time[pubdate]"

SIDEARM_STORY_PUBLISHED_TIME_FALLBACK = ".sidearm-story-template-date time"
