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
}
