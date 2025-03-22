import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from src.services import GameService, TeamService
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game
from src.utils.helpers import get_dominant_color
import base64
import html
import pytz

def extract_season_years(page_title):
    """
    Extracts season years from page title
    If title is across years like '2024-25', it returns (first_year, second_year)
    If single year, returns (year, None).
    """
    match = re.search(r"(\d{4})(?:-(\d{2}))?", page_title)
    if match:
        first_year = match.group(1)
        second_year = None
        if match.group(2):
            second_year = first_year[:2] + match.group(2)
        return first_year, second_year
    return None, None

def infer_game_year(date_text, season_years):
    """
    Determines the calendar year for a game based on month
    August to December belong to the first year
    """
    first_year, second_year = season_years
    month_abbr = date_text[:3]
    if second_year:
        if month_abbr in ("Aug", "Sep", "Oct", "Nov", "Dec"):
            return first_year
        else:
            return second_year
    return first_year

def parse_time_string(time_str):
    if not time_str:
        return None
        
    print(f"Parsing time: '{time_str}'")
    
    # More robust time parsing
    time_str = time_str.strip().lower()
    
    # Handle various formats
    time_str = time_str.replace("p.m.", "pm").replace("a.m.", "am")
    time_str = time_str.replace("p. m.", "pm").replace("a. m.", "am")
    time_str = time_str.replace(" pm", "pm").replace(" am", "am")
    
    # Handle 24-hour format
    hour24_pattern = re.compile(r'(\d{1,2}):(\d{2})(?!\s*[ap])')
    match24 = hour24_pattern.search(time_str)
    if match24:
        hours = int(match24.group(1))
        minutes = match24.group(2)
        
        # Convert to 12-hour format
        if hours >= 12:
            am_pm = "PM"
            if hours > 12:
                hours -= 12
        else:
            am_pm = "AM"
            if hours == 0:
                hours = 12
        
        return f"{hours}:{minutes} {am_pm}"
    
    # Regular 12-hour format
    time_pattern = re.compile(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', re.IGNORECASE)
    match = time_pattern.search(time_str)
    
    if not match:
        print(f"No match found for time pattern in: '{time_str}'")
        return None
        
    hours = int(match.group(1))
    minutes = match.group(2) or "00"
    am_pm = match.group(3) or "PM"  # Default to PM if not specified
    
    return f"{hours}:{minutes} {am_pm.upper()}"

def convert_to_utc(date_str, time_str, eastern_tz=pytz.timezone('US/Eastern')):
    """
    Convert date and time strings to UTC datetime.
    
    Args:
        date_str (str): Date string like "Aug 31 (Sat) 2024"
        time_str (str): Time string like "12:00 PM"
        eastern_tz: Eastern timezone object (Cornell is in Eastern Time)
        
    Returns:
        datetime: UTC datetime object or None if parsing fails
    """
    print(f"Converting: date='{date_str}', time='{time_str}'")
    if not date_str:
        return None
        
    try:
        # Clean up date string - remove day of week in parentheses
        date_str = re.sub(r'\([^)]*\)', '', date_str).strip()
        
        # Parse the standardized time
        standardized_time = parse_time_string(time_str)
        
        if standardized_time:
            print(f"Standardized time: {standardized_time}")
            # Combine date and time
            datetime_str = f"{date_str} {standardized_time}"
            # Try different date formats
            for fmt in ["%b %d %Y %I:%M %p", "%B %d %Y %I:%M %p", "%b. %d %Y %I:%M %p"]:
                try:
                    # Parse as Eastern Time
                    local_dt = eastern_tz.localize(datetime.strptime(datetime_str, fmt))
                    # Convert to UTC
                    return local_dt.astimezone(timezone.utc)
                except ValueError:
                    continue
        else:
            print(f"Failed to standardize time: {time_str}")
        
        # If time parsing fails, just use the date at midnight
        for fmt in ["%b %d %Y", "%B %d %Y", "%b. %d %Y"]:
            try:
                local_dt = eastern_tz.localize(datetime.strptime(date_str, fmt).replace(hour=0, minute=0))
                return local_dt.astimezone(timezone.utc)
            except ValueError:
                continue
                
    except Exception as e:
        print(f"Error converting date/time to UTC: {e} for date={date_str}, time={time_str}")
    
    return None

def fetch_game_schedule():
    """
    Scrape the game schedule from the given URLs and store the data in the database.
    """
    for sport, data in SPORT_URLS.items():
        url = SCHEDULE_PREFIX + sport + SCHEDULE_POSTFIX
        parse_schedule_page(url, data["sport"], data["gender"])

def parse_schedule_page(url, sport, gender):
    """
    Parse the game schedule page and store the data in the database.
    Args:
        url (str): The URL of the game schedule page.
        sport (str): The sport of the games.
        gender (str): The gender of the games.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    page_title = soup.title.text.strip() if soup.title else ""
    season_years = extract_season_years(page_title)

    for game_item in soup.select(GAME_TAG):
        game_data = {}
        game_data["gender"] = gender
        game_data["sport"] = sport

        opponent_name_tag = game_item.select_one(OPPONENT_NAME_TAG_A)
        opponent_name = (
            opponent_name_tag.text.strip()
            if opponent_name_tag
            else game_item.select_one(OPPONENT_NAME_TAG).text.strip()
        )
        game_data["opponent_name"] = opponent_name

        opponent_logo_tag = game_item.select_one(OPPONENT_LOGO_TAG)
        opponent_logo = (
            opponent_logo_tag[OPPONENT_LOGO_URL_ATTR] if opponent_logo_tag else None
        )
        game_data["opponent_logo"] = (
            BASE_URL + opponent_logo if opponent_logo else None
        )

        date_tag = game_item.select_one(DATE_TAG)
        if date_tag:
            date_text = date_tag.get_text(strip=True)
        else:
            date_text = ""

        time_tag = game_item.select_one(TIME_TAG)
        time_text = time_tag.text.strip() if time_tag else None
        
        game_year = infer_game_year(date_text, season_years)
        if date_text and game_year:
            full_date_text = f"{date_text} {game_year}"
            # Store the formatted date string for lookup purposes
            game_data["date"] = full_date_text
            # Also store UTC datetime
            game_data["utc_date"] = convert_to_utc(full_date_text, time_text)
        else:
            game_data["date"] = date_text
            game_data["utc_date"] = None

        game_data["time"] = time_text

        location_tag = game_item.select_one(LOCATION_TAG)
        game_data["location"] = location_tag.text.strip() if location_tag else None

        result_tag = game_item.select_one(RESULT_TAG)
        if result_tag:
            game_data["result"] = result_tag.text.strip().replace("\n", "")
        else:
            game_data["result"] = None
            
        box_score_tag = game_item.select_one(BOX_SCORE_TAG)
        if box_score_tag:
            box_score_link = box_score_tag["href"]
            game_details = scrape_game(f"{BASE_URL}{box_score_link}", sport.lower())
            if game_details.get('error') == 'Sport parser not found':
                game_data["box_score"] = None
                game_data["score_breakdown"] = None
            else:
                game_data["box_score"] = game_details.get("scoring_summary")
                game_data["score_breakdown"] = game_details.get("scores")
        else:
            game_data["box_score"] = None
            game_data["score_breakdown"] = None

        process_game_data(game_data)


def process_game_data(game_data):
    """
    Process the game data and store it in the database.

    Args:
        game_data (dict): A dictionary containing the game data.
    """
    location_data = game_data["location"].split("\n")
    geo_location = location_data[0]
    if (",") not in geo_location:
        city = geo_location
        state = geo_location
    else:
        city, state = map(str.strip, geo_location.split(","))
    location = location_data[1] if len(location_data) > 1 else None

    team = TeamService.get_team_by_name(game_data["opponent_name"])
    if not team:
        color = (
            get_dominant_color(game_data["opponent_logo"])
            if game_data["opponent_logo"]
            else "#FFFFFF"
        )
        encoded_opponent_logo = ""
        if game_data["opponent_logo"]:
            try:
                response = requests.get(game_data["opponent_logo"])
                response.raise_for_status()
                encoded_opponent_logo = base64.b64encode(response.content).decode('utf-8')
            except Exception as e:
                print(f"Error fetching encoded opponent logo: {e}")
        team_data = {
            "color": color,
            "image": game_data["opponent_logo"],
            "b64_image": encoded_opponent_logo,
            "name": game_data["opponent_name"],
        }
        team = TeamService.create_team(team_data)

    # Format the UTC date as ISO string if it exists
    if game_data["utc_date"] is not None:
        utc_date_str = game_data["utc_date"].isoformat()
        print(f"UTC date converted to ISO string: {utc_date_str}")
    else:
        utc_date_str = None
        print(f"UTC date is None for game: {game_data['sport']} against {game_data['opponent_name']} on {game_data['date']}")

    curr_game = GameService.get_game_by_data(
        city,
        game_data["date"],
        game_data["gender"],
        location,
        team.id,
        game_data["sport"],
        state,
        game_data["time"],
    )
    if curr_game:
        updates = {}
        if curr_game.result != game_data["result"]:
            updates["result"] = game_data["result"]
        if curr_game.box_score != game_data["box_score"]:
            updates["box_score"] = game_data["box_score"]
            updates["score_breakdown"] = game_data["score_breakdown"]
        
        if utc_date_str:
            # Check if the current UTC date is different or missing
            current_utc = getattr(curr_game, "utc_date", None)
            print(f"Current UTC in DB: {current_utc}, New UTC: {utc_date_str}")
            if current_utc != utc_date_str:
                updates["utc_date"] = utc_date_str
                print(f"Updating utc_date from '{current_utc}' to '{utc_date_str}'")
        else:
            print(f"Not updating utc_date because new value is None")
        
        if updates:
            print(f"Updating game with fields: {list(updates.keys())}")
            GameService.update_game(curr_game.id, updates)
        return