import logging
import time
import requests
from PIL import Image
from io import BytesIO
from collections import Counter
import re
import threading
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_with_retries(
    url,
    max_retries=3,
    timeout=15,
    backoff_factor=1.5,
    **kwargs,
):
    """
    GET request with retries on connection errors (ChunkedEncodingError, ConnectionResetError, etc.).
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=timeout, **kwargs)
            r.raise_for_status()
            return r
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            ConnectionResetError,
        ) as e:
            last_error = e
            if attempt < max_retries - 1:
                sleep_secs = backoff_factor ** attempt
                logger.warning(
                    "Request failed (attempt %s/%s), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    sleep_secs,
                    e,
                )
                time.sleep(sleep_secs)
            else:
                raise last_error
    raise last_error

def get_dominant_color(image_url, white_threshold=200, black_threshold=50):
    """
    Get the hex code of the dominant color of an image.

    Args:
        image_url (str): The URL of the image.
        white_threshold (int): The threshold for white pixels. (optional)
        black_threshold (int): The threshold for black pixels. (optional)

    Returns:
        color: The hex code of the dominant color.
    """
    default_color = "#000000" 

    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGBA")

        image = image.resize((50, 50))
        image = image.quantize(colors=5).convert("RGBA")
        pixels = image.getdata()

        filtered_pixels = [
            pixel
            for pixel in pixels
            if not (
                pixel[0] > white_threshold
                and pixel[1] > white_threshold
                and pixel[2] > white_threshold
            )
            and not (
                pixel[0] < black_threshold
                and pixel[1] < black_threshold
                and pixel[2] < black_threshold
            )
        ]

        if filtered_pixels:
            pixel_count = Counter(filtered_pixels)
            dominant_color = pixel_count.most_common(1)[0][0]
        else:
            dominant_color = (0, 0, 0)

        hex_color = "#{:02x}{:02x}{:02x}".format(
            dominant_color[0], dominant_color[1], dominant_color[2]
        )
        return hex_color
    except Exception as e:
        logging.error(f"Error in get_dominant_color for {image_url}: {e}")
        return default_color
    
def normalize_game_data(data: dict):
    """
    Normalize placeholder values like TBA/TBD into None.
    """
    placeholders = {"TBA", "TBD", "tba", "tbd"}

    for field in ["time", "city", "state"]:
        if data.get(field) in placeholders:
            data[field] = None

    return data

def is_tournament_placeholder_team(team_name: str):
    """
    Check if a team name is a tournament placeholder.
    """
    
    placeholder_team_names = [
        "First Round", "Second Round", "Third Round", "Quarterfinals",
        "College Cup Semifinals", "College Cup Championship Game",
        "ECAC Hockey First Round", "ECAC Hockey Quarterfinals",
        "ECAC Hockey Semifinals", "ECAC Hockey Championship Game",
        "Regional Semifinals", "Regional Championship", "National Semifinals",
        "TBD", "National Championship", "NCAA Wrestling Championships", "NCAA Northeast Regional CHampionships",
        "NCAA Cross Country Championships", 
    ]
    return team_name in placeholder_team_names

def is_cornell_loss(result: str):
    """
    Check if the result indicates a Cornell loss.
    """
    
    if not result:
        return False
    
    # Common loss indicators in result strings
    loss_indicators = ["L", "Loss", "loss", "Defeated", "defeated"]
    return any(indicator in result for indicator in loss_indicators)

def extract_sport_from_title(title):
    """
    Extracts the sport type from a YouTube video title.
    
    Args:
        title (str): The title of the YouTube video
        
    Returns:
        str: The sport type if found, None otherwise
    """
    if not title:
        return None
    
    title_lower = title.lower()
    
    sport_patterns = [
        # Ice Hockey
        (r"ice\s+hockey", "Ice Hockey"),
        (r"women'?s\s+ice\s+hockey", "Ice Hockey"),
        (r"men'?s\s+ice\s+hockey", "Ice Hockey"),
        # Field Hockey
        (r"field\s+hockey", "Field Hockey"),
        # Hockey
        (r"\bhockey\b", "Ice Hockey"),
        # Basketball
        (r"basketball", "Basketball"),
        # Football
        (r"\bfootball\b", "Football"),
        # Soccer
        (r"\bsoccer\b", "Soccer"),
        # Volleyball
        (r"volleyball", "Volleyball"),
        # Wrestling
        (r"wrestling", "Wrestling"),
        # Sprint Football
        (r"sprint\s+football", "Sprint Football"),
    ]
    
    for pattern, sport_name in sport_patterns:
        if re.search(pattern, title_lower):
            return sport_name
    
    if "ice" in title_lower and ("hockey" in title_lower or "cornell" in title_lower):
        return "Ice Hockey"
    
    return None

def extract_sport_type_from_title(title: str):
    """
    Extract the sport type from an article title by matching against known sports.
    
    Args:
        title (str): The article title to analyze
        
    Returns:
        str: The sport name if found, otherwise "sports" as default
    """
    from .constants import SPORT_URLS
    
    if not title:
        return "sports"
    
    # Get all unique sport names from SPORT_URLS
    sport_names = set()
    for sport_data in SPORT_URLS.values():
        sport_name = sport_data["sport"].strip()
        if sport_name:
            sport_names.add(sport_name)
    
    # Sort by length (longest first) to match "Swimming & Diving" before "Swimming"
    sport_names_sorted = sorted(sport_names, key=len, reverse=True)
    
    title_lower = title.lower()
    
    for sport_name in sport_names_sorted:
        if sport_name.lower() in title_lower:
            return sport_name
    
    # Special mappings for common variations in titles
    # Only checked if no exact match found above
    # e.g., "Hockey" in title should match "Ice Hockey" in sport names
    special_mappings = {
        "hockey": "Ice Hockey",  # "Men's Hockey" or "Women's Hockey" → "Ice Hockey"
    }
    
    for keyword, sport_name in special_mappings.items():
        if keyword in title_lower and sport_name in sport_names:
            return sport_name
    
    return "sports"

def sidearm_dates_match(db_date: str, sidearm_date: str) -> bool:
        """
        Check if two date strings represent the same date.
        
        Args:
            db_date: Date from our database
            sidearm_date: Date from Sidearm API
            
        Returns:
            True if dates match, False otherwise
        """
        try:
            # Parse Sidearm date (format: "9/29/2025")
            sidearm_dt = datetime.strptime(sidearm_date, "%m/%d/%Y")
            
            numToMonth = {
                "1": "Jan",
                "2": "Feb",
                "3": "Mar",
                "4": "Apr",
                "5": "May",
                "6": "Jun",
                "8": "Aug",
                "9": "Sep",
                "10": "Oct",
                "11": "Nov",
                "12": "Dec"
            }
            
            year = str(sidearm_dt.year)
            month = numToMonth[str(sidearm_dt.month)]
            date = str(sidearm_dt.day)
            
            # This is simple check - might need to improve this
            if month in db_date and date in db_date and year in db_date:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error comparing dates: {str(e)}")
            return False

def is_game_active(game_data: Dict) -> bool:
        """
        Check if a game is currently active (started but not completed).
        
        Args:
            game_data: Game data from Sidearm API
            
        Returns:
            True if game is active, False otherwise
        """
        if not game_data or 'Game' not in game_data:
            return False
        
        game = game_data['Game']
        return (
            game.get('HasStarted', False) and 
            not game.get('IsComplete', False)
        )

# Sidearm sport codes that use volleyball rally scoring: every rally ends in a
# point for one side, there is no game clock, and Period is the set number.
VOLLEYBALL_SPORT_CODES = {"wvball", "mvball"}

# Play types that end a volleyball rally. Only used when the feed omits the
# per-play Score object, since that object is the more reliable signal. Roster and
# stoppage entries in the play log ("UNH subs: ...", "Timeout UNH.",
# "UNH starters: ...") match none of these and so stay out of the box score.
VOLLEYBALL_SCORING_KEYWORDS = [
    'KILL', 'ACE', 'ATTACK', 'BLOCK', 'SERVICE', 'ERROR', 'HIT', 'SPIKE',
]

# Play descriptions that count as scoring plays in the clock-based sports.
SCORING_KEYWORDS = ['GOAL', 'SCORE', 'TOUCHDOWN', 'FIELD GOAL', 'SHOT']


def convert_play_to_our_format(play: Dict, game: Dict) -> Optional[Dict]:
        """
        Convert a Sidearm play to our box score format.

        Keys are snake_case to match BoxScoreEntryType and the box scores built by
        game_details_scrape, so live plays read back through GraphQL the same way
        scraped ones do.

        Args:
            play: Play data from Sidearm API
            game: Game data from Sidearm API

        Returns:
            Play in our format or None if conversion fails
        """
        try:
            # Extract basic play information
            description = play.get('Narrative', '')
            period = play.get('Period', 1)

            # Determine which team scored
            home_team = game.get('HomeTeam', {})
            visiting_team = game.get('VisitingTeam', {})
            cornell_is_home = home_team.get('Name', '').upper() == 'CORNELL'

            is_volleyball = game.get('GlobalSportShortname', '') in VOLLEYBALL_SPORT_CODES

            # Sidearm attaches a Score object to exactly the plays that changed the
            # score, so its presence identifies a scoring play without having to
            # read the narrative. Fall back to keywords when it is absent.
            play_score = play.get('Score')
            if isinstance(play_score, dict):
                is_scoring_play = True
            elif is_volleyball:
                is_scoring_play = any(
                    keyword in description.upper() for keyword in VOLLEYBALL_SCORING_KEYWORDS
                )
            else:
                is_scoring_play = any(
                    keyword in description.upper() for keyword in SCORING_KEYWORDS
                )

            if not is_scoring_play:
                return None

            # Volleyball has no clock - ClockSeconds is -1 on every play.
            time = None if is_volleyball else convert_seconds_to_time(play.get('ClockSeconds', 0))

            # Prefer the per-play score, which is the score *after* this play. The
            # team-level score is only the current value, so using it would stamp
            # every play in a batch with the same score. For volleyball this is the
            # running score within the current set.
            if isinstance(play_score, dict):
                home_score = play_score.get('HomeTeam', 0)
                visiting_score = play_score.get('VisitingTeam', 0)
            else:
                home_score = home_team.get('Score', 0)
                visiting_score = visiting_team.get('Score', 0)

            cor_score = home_score if cornell_is_home else visiting_score
            opp_score = visiting_score if cornell_is_home else home_score

            # Sidearm names the team that won the point as "HomeTeam"/"VisitingTeam".
            scoring_team = (play.get('Team') or '').replace(' ', '')
            if scoring_team == 'HomeTeam':
                team = 'COR' if cornell_is_home else 'OPP'
            elif scoring_team == 'VisitingTeam':
                team = 'OPP' if cornell_is_home else 'COR'
            else:
                team = ''

            return {
                'play_id': play.get('Id'),
                'cor_score': cor_score,
                'opp_score': opp_score,
                'team': team,
                'period': period,
                'time': time,
                'description': description,
                'scorer': None,
                'assist': None,
                'score_by': None
            }

        except Exception as e:
            logger.error(f"Error converting play: {str(e)}")
            return None

def convert_seconds_to_time(seconds: int) -> str:
    """
    Convert total seconds to "minute:seconds" format (e.g. 90 -> "1:30", 65 -> "1:05").
    """
    if seconds is None or seconds < 0:
        return "0:00"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"

# Maps a school's public hostname (e.g. "binghamtonbearcats.com") to its folder on
# sidearmstats.com (e.g. "binghamton"). Populated lazily by
# resolve_sidearm_stats_folder; the mapping is stable per school, and the live
# scraper runs every 30s, so caching avoids refetching the stats page each cycle.
_SIDEARM_FOLDER_CACHE: Dict[str, Optional[str]] = {}
_SIDEARM_FOLDER_CACHE_LOCK = threading.Lock()

# The stats page embeds the sidearmstats.com folder in an inline script. The
# Angular livestats app reads livestats_foldername to build its own JSON URLs, so
# that is the authoritative value; client_shortname usually matches but not always
# (brownbears.com reports "brownuni" while the real folder is "brown").
_LIVESTATS_FOLDER_PATTERNS = [
    re.compile(r"""livestats_foldername\s*=\s*["']([^"']+)["']"""),
    re.compile(r"""client_shortname\s*=\s*["']([^"']+)["']"""),
]


def parse_sidearm_stats_url(stats_url: str):
    """
    Pull the sidearmstats folder and sport code out of a live stats URL.

    Two shapes appear in the Cornell calendar feed:
      - the school's own site, e.g. "https://binghamtonbearcats.com/sidearmstats/wvball/summary",
        where the folder is not in the URL at all and has to be read off the page
      - sidearmstats.com directly, e.g. "http://www.sidearmstats.com/cornell/football/index.html",
        where the folder is the first path segment

    Args:
        stats_url (str): The live stats URL from the calendar feed.

    Returns:
        tuple: (folder, sport_code), either of which may be None if not present
               in the URL. A None folder means it must be resolved from the page.
    """
    if not stats_url:
        return None, None

    parsed = urlparse(stats_url)
    host = (parsed.netloc or "").lower()
    segments = [segment for segment in (parsed.path or "").split("/") if segment]

    # sidearmstats.com/<folder>/<sport>/...
    if host.endswith("sidearmstats.com"):
        folder = segments[0] if segments else None
        sport_code = segments[1] if len(segments) > 1 else None
        return folder, sport_code

    # <school>.com/sidearmstats/<sport>/... - folder lives in the page, not the URL
    if "sidearmstats" in segments:
        index = segments.index("sidearmstats")
        sport_code = segments[index + 1] if len(segments) > index + 1 else None
        return None, sport_code

    return None, None


def resolve_sidearm_stats_folder(stats_url: str) -> Optional[str]:
    """
    Find the sidearmstats.com folder for a school-hosted live stats page.

    There is no derivable pattern between a school's hostname and its folder
    (binghamtonbearcats.com -> "binghamton", ohiostatebuckeyes.com ->
    "ohiostatedev"), so the page is fetched once per host and the folder is read
    out of the inline script that configures the livestats app.

    Args:
        stats_url (str): The school-hosted live stats URL.

    Returns:
        str: The sidearmstats.com folder, or None if it could not be determined.
    """
    host = (urlparse(stats_url).netloc or "").lower()
    if not host:
        return None

    with _SIDEARM_FOLDER_CACHE_LOCK:
        if host in _SIDEARM_FOLDER_CACHE:
            return _SIDEARM_FOLDER_CACHE[host]

    folder = None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html,application/xhtml+xml",
        }
        response = get_with_retries(stats_url, headers=headers, timeout=15)
        for pattern in _LIVESTATS_FOLDER_PATTERNS:
            match = pattern.search(response.text)
            if match:
                folder = match.group(1).strip()
                break
        if not folder:
            logger.warning("No livestats folder found on stats page %s", stats_url)
    except Exception as e:
        logger.error("Error resolving sidearm stats folder for %s: %s", stats_url, e)
        # Don't cache transient failures - a later cycle should retry the fetch.
        return None

    with _SIDEARM_FOLDER_CACHE_LOCK:
        _SIDEARM_FOLDER_CACHE[host] = folder
    return folder


def build_sidearm_game_json_url(stats_url: str, sport_code: Optional[str] = None) -> Optional[str]:
    """
    Build the sidearmstats.com game.json URL that backs a live stats page.

    Args:
        stats_url (str): The live stats URL from the calendar feed.
        sport_code (str): Sidearm's global sport shortname (e.g. "wvball"). Taken
                          from the calendar event when available since it is more
                          reliable than the URL path; falls back to the URL.

    Returns:
        str: The game.json URL, or None if the folder or sport could not be found.
    """
    url_folder, url_sport_code = parse_sidearm_stats_url(stats_url)
    sport_code = sport_code or url_sport_code

    # Only fetch the page when the URL really is a livestats page but doesn't
    # carry the folder itself, so an unrelated stats link costs no request.
    folder = url_folder
    if not folder and url_sport_code:
        folder = resolve_sidearm_stats_folder(stats_url)

    if not folder or not sport_code:
        logger.warning(
            "Could not build game.json URL for %s (folder=%s, sport=%s)",
            stats_url,
            folder,
            sport_code,
        )
        return None

    return f"https://sidearmstats.com/{folder}/{sport_code}/game.json"
