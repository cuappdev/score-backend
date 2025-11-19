import logging
import requests
from PIL import Image
from io import BytesIO
from collections import Counter


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
