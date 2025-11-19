import logging
import requests
from PIL import Image
from io import BytesIO
from collections import Counter
import re


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

