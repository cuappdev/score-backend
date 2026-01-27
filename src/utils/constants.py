# Prefix for opponent image URLs
IMAGE_PREFIX = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/cornellbigred.com"

# Base URL
BASE_URL = "https://cornellbigred.com"

# The tag for each game
GAME_TAG = ".sidearm-calendar-schedule-event"

# The tag for each opponent name with a
OPPONENT_NAME_TAG_A = ".sidearm-schedule-game-opponent-name a"

# The tag for each opponent name
OPPONENT_NAME_TAG = ".sidearm-schedule-game-opponent-name"

# The tag for each opponent image
OPPONENT_LOGO_TAG = ".sidearm-schedule-game-opponent-logo img"

# The attribute for the opponent image URL
OPPONENT_LOGO_URL_ATTR = "data-src"

# The tag for each date
DATE_TAG = ".sidearm-schedule-game-opponent-date span"

# The tag for each time
TIME_TAG = ".sidearm-schedule-game-opponent-date span + span"

# The tag for each location
LOCATION_TAG = ".sidearm-schedule-game-location"

# The prefix for the sports schedules
SCHEDULE_PREFIX = "https://cornellbigred.com/calendar?vtype=list/"

# The tag for each result
RESULT_TAG = ".sidearm-schedule-game-result"

# The tag for the box score
BOX_SCORE_TAG = ".sidearm-schedule-game-links-boxscore a"

# The tag for the game ticket link
GAME_TICKET_LINK = ".sidearm-schedule-game-links-tickets a"

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
CLASS_HIDE_ON_LARGE_DOWN = 'hide-on-large-down'
CLASS_HIDE_ON_SMALL_DOWN = 'hide-on-small-down'
CLASS_SCORING_SUMMARY = 'scoring-summary'
CLASS_OVERALL_STATS = 'overall-stats'
CLASS_PLAY_BY_PLAY = 'play-by-play'
CLASS_BOX_SCORE = 'box-score'

# HTML Attributes
ATTR_ARIA_LABEL = 'aria-label'
ATTR_ALT = 'alt'
ATTR_ID = 'id'

# HTML IDs for Sections
ID_BOX_SCORE = 'box-score'
ID_PERIOD_1 = 'period-1'
ID_PERIOD_2 = 'period-2'
ID_SET_1 = 'set-1'
ID_SET_2 = 'set-2'
ID_SET_3 = 'set-3'
ID_SET_4 = 'set-4'
ID_SET_5 = 'set-5'

# Labels
LABEL_SCORING_SUMMARY = 'Scoring Summary'
LABEL_CU = 'CU'

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

MENS_EXCLUSIVE_SPORTS = ["wrestling", "football", "baseball", "golf", "sprint football"]
WOMENS_EXCLUSIVE_SPORTS = ["softball", "fencing", "equestrian", "volleyball", "sailing", "field hockey", "gymnastics"]

IMAGE_BASE_URL = (
    "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/cornellbigred.com"
)

# Cornell Sports YouTube Channel ID
CHANNEL_ID = "UClSQOi2gnn9bi7mcgQrAVKA"

# The maximum number of videos to retrieve
VIDEO_LIMIT = 20

ARTICLE_IMG_TAG = ".dom-art-container img"
