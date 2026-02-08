import logging
import requests
from PIL import Image
from io import BytesIO
from collections import Counter
import re
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

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

def convert_play_to_our_format(self, play: Dict, game: Dict) -> Optional[Dict]:
        """
        Convert a Sidearm play to our box score format.
        
        Args:
            play: Play data from Sidearm API
            game: Game data from Sidearm API
            
        Returns:
            Play in our format or None if conversion fails
        """
        try:
            # Extract basic play information
            description = play.get('Narrative', '')
            time = convert_seconds_to_time(play.get('ClockSeconds', 0))
            period = play.get('Period', 1)
            
            # Determine which team scored
            home_team = game.get('HomeTeam', {})
            visiting_team = game.get('VisitingTeam', {})

            scoring_team = play.get('Team', "")
            
            # Check if it's a scoring play
            is_scoring_play = any(keyword in description.upper() for keyword in ['GOAL', 'SCORE', 'TOUCHDOWN', 'FIELD GOAL', 'SHOT'])
            
            if not is_scoring_play:
                return None
            
            # Determine team and scores
            if (scoring_team == "Visiting Team" and visiting_team.get('Name', '').upper() == 'CORNELL') or (scoring_team == "Home Team" and home_team.get('Name', '').upper() == 'CORNELL'):
                team = 'COR'
                # Get current scores
                cor_score = home_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else visiting_team.get('Score', 0)
                opp_score = visiting_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else home_team.get('Score', 0)
            else:
                team = 'OPP'
                # Get current scores
                cor_score = home_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else visiting_team.get('Score', 0)
                opp_score = visiting_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else home_team.get('Score', 0)
            
            if scoring_team == "":
                team = ""

            return {
                'corScore': cor_score,
                'oppScore': opp_score,
                'team': team,
                'period': period,
                'time': time,
                'description': description,
                'scorer': None,
                'assist': None,
                'scoreBy': None
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
