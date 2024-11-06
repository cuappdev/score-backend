# Prefix for opponent image URLs
IMAGE_PREFIX = "https://cornellbigred.com"

# The tag for each game
GAME_TAG = ".sidearm-schedule-game"

# The tag for each opponent name
OPPONENT_NAME_TAG = ".sidearm-schedule-game-opponent-name a"

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
SCHEDULE_PREFIX = "https://cornellbigred.com/sports/"

# The postfix for the sports schedules
SCHEDULE_POSTFIX = "/schedule"

# The tag for each result
RESULT_TAG = ".sidearm-schedule-game-result"

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

IMAGE_BASE_URL = (
    "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/cornellbigred.com"
)