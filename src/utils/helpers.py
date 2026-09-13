import logging
import requests
from PIL import Image
from io import BytesIO
from collections import Counter
import re
from urllib.parse import urljoin, urlparse

from src.utils.constants import ALLOWED_URL_HOSTS, ALLOWED_URL_SCHEMES, BASE_URL


PLACEHOLDER_VALUES = {
    "",
    "tba",
    "tbd"
}


def is_allowed_url(url):
    """Allow only HTTP(S) URLs hosted by approved Cornell/Sidearm domains."""
    if not url:
        return False
    parsed = urlparse(str(url))
    hostname = (parsed.hostname or "").casefold().rstrip(".")
    return (
        parsed.scheme.casefold() in ALLOWED_URL_SCHEMES
        and hostname in ALLOWED_URL_HOSTS
    )


def safe_absolute_url(link, base_url=BASE_URL):
    """Resolve a link and return it only when its destination is approved."""
    if not link:
        return None
    normalized = urljoin(base_url, str(link))
    if not is_allowed_url(normalized):
        logging.warning("Skipping unapproved URL: %s", normalized)
        return None
    return normalized


def normalize_placeholder(value, fallback="TBA"):
    """Return a stable value for blank/unknown source fields."""
    if value is None:
        return fallback

    normalized = " ".join(str(value).split())
    if normalized.casefold() in PLACEHOLDER_VALUES:
        return fallback
    return normalized


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

    if not is_allowed_url(image_url):
        logging.warning("Skipping unapproved image URL: %s", image_url)
        return default_color

    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
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
    Normalize placeholder values consistently before matching or persistence.

    Named tournament labels are deliberately not included in the placeholder
    set, so values such as "Quarterfinals" remain available for display and
    tournament-team handling.
    """

    for field in ["time", "city", "state", "location", "opponent_name"]:
        if field in data:
            data[field] = normalize_placeholder(data.get(field))

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
        "TBA", "TBD", "National Championship", "NCAA Wrestling Championships", "NCAA Northeast Regional CHampionships",
        "NCAA Cross Country Championships", 
    ]
    return team_name in placeholder_team_names

def is_cornell_loss(result: str):
    """
    Check if the result indicates a Cornell loss.
    """
    
    if not result:
        return False
    
    # Match the result token rather than substrings (for example, the word
    # "Cancelled" must not be treated as a loss because it contains "L").
    normalized = " ".join(str(result).split()).casefold()
    return bool(re.match(r"^(?:l|loss|defeated)\b", normalized))

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
