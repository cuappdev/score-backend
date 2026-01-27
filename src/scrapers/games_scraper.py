import requests
from bs4 import BeautifulSoup
from src.services import GameService, TeamService
from src.utils.convert_to_utc import convert_to_utc
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game
from src.utils.helpers import get_dominant_color, normalize_game_data, is_tournament_placeholder_team, is_cornell_loss
import base64
import re
from src.database import db
import threading
from datetime import date, timedelta, datetime

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

def fetch_game_schedule():
    """
    Scrape the game schedule from the given URLs in parallel using threads.
    Each sport is scraped in its own thread for improved performance.
    """
    url = SCHEDULE_PREFIX

    # create single thread for all sports
    thread = threading.Thread(
        target=parse_schedule_page,
        args=(url,),
        name=f"Scraper"
    )
    thread.daemon = True
    thread.start()

def parse_schedule_page(url):
    """
    Parse the game schedule page and store the data in the database.
    Args:
        url (str): The URL of the game schedule page.
        sport (str): The sport of the games.
        gender (str): The gender of the games.
    """
    today = date.today()
    days_since_saturday = (today.weekday() - 5) % 7

    # go back to most recent saturday
    last_saturday = today - timedelta(days=days_since_saturday)

    params = {
        "type": "events",
        "sport": 0,
        "location": "all",
        "date": last_saturday.strftime("%Y-%m-%dT00:00:00"),
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://cornellbigred.com/calendar?vtype=list/",
    }

    url = "https://cornellbigred.com/services/responsive-calendar.ashx"
    r = requests.get(url, params=params, headers=headers, timeout=10)
    data = r.json()

    for day in data:
        if day.get("events"):
            for game in day["events"]:
                game_data = {}
               
                sport_info = game.get("sport", {})
                sport_title = sport_info.get("title", "")
                
                if not sport_title:
                    continue  
               
                sport_lower = sport_title.lower()
                if "women's" in sport_lower:
                    game_data["gender"] = "Womens"
                    sport_name = re.sub(r"women's\s*", "", sport_title, flags=re.IGNORECASE).strip()
                elif "men's" in sport_lower:
                    game_data["gender"] = "Mens"
                    sport_name = re.sub(r"men's\s*", "", sport_title, flags=re.IGNORECASE).strip()
                elif "women" in sport_lower:
                    game_data["gender"] = "Womens"
                    sport_name = re.sub(r"women\s*", "", sport_title, flags=re.IGNORECASE).strip()
                elif "men" in sport_lower:
                    game_data["gender"] = "Mens"
                    sport_name = re.sub(r"men\s*", "", sport_title, flags=re.IGNORECASE).strip()
                else:
                    sport_shortname = sport_info.get("shortname", "").lower()
                    sport_title_lower = sport_title.lower()

                    is_mens_exclusive = False
                    for exclusive in MENS_EXCLUSIVE_SPORTS:
                        exclusive_lower = exclusive.lower()
                        if exclusive_lower in sport_title_lower or exclusive_lower in sport_shortname:
                            game_data["gender"] = "Mens"
                            sport_name = sport_title
                            is_mens_exclusive = True
                            break
                    
                    if not is_mens_exclusive:
                        is_womens_exclusive = False
                        for exclusive in WOMENS_EXCLUSIVE_SPORTS:
                            exclusive_lower = exclusive.lower()
                            if exclusive_lower in sport_title_lower or exclusive_lower in sport_shortname:
                                game_data["gender"] = "Womens"
                                sport_name = sport_title
                                is_womens_exclusive = True
                                break
                        
                        if not is_womens_exclusive:
                            game_data["gender"] = "Mens"
                            sport_name = sport_title
                
                game_data["sport"] = sport_name.strip()
                
                opponent = game.get("opponent", {})
                game_data["opponent_name"] = opponent.get("title", "")
                
                if not game_data["opponent_name"]:
                    continue
                
                opponent_image = opponent.get("image", {})
                if opponent_image:
                    image_path = opponent_image.get("path", "")
                    image_filename = opponent_image.get("filename", "")
                    if image_path and image_filename:
                        path = image_path.lstrip("/")
                        game_data["opponent_logo"] = f"{BASE_URL}/{path}/{image_filename}"
                    else:
                        game_data["opponent_logo"] = None
                else:
                    game_data["opponent_logo"] = None
                  
                event_date = game.get("date", "")
                event_time = game.get("time", "")
                
                if event_date:
                    # Parse ISO date format: "2026-01-24T12:00:00"
                    try:
                        date_clean = event_date.split('.')[0].replace('Z', '')
                        dt = datetime.strptime(date_clean, "%Y-%m-%dT%H:%M:%S")
                        game_data["date"] = f"{dt.strftime('%b')} {dt.day} ({dt.strftime('%a')}) {dt.strftime('%Y')}"                 
                        game_data["utc_date"] = convert_to_utc(game_data["date"], event_time)
                    except Exception as e:
                        print(f"Error parsing date {event_date}: {e}")
                        game_data["date"] = event_date
                        game_data["utc_date"] = None
                else:
                    game_data["date"] = ""
                    game_data["utc_date"] = None
                
                game_data["time"] = event_time if event_time else None
               
                game_data["location"] = game.get("location", "")
               
                result_info = game.get("result", {})
                if result_info and isinstance(result_info, dict):
                    status = result_info.get("status", "")
                    team_score = result_info.get("team_score", "")
                    opponent_score = result_info.get("opponent_score", "")
                 
                    if status:
                        if team_score is not None and opponent_score is not None:
                            game_data["result"] = f"{status} {team_score}-{opponent_score}"
                        else:
                            game_data["result"] = status
                    else:
                        game_data["result"] = None
                else:
                    game_data["result"] = None
                
                box_score_info = None
                if result_info and isinstance(result_info, dict):
                    box_score_info = result_info.get("boxscore")
              
                media = game.get("media", {})
                ticket_info = media.get("tickets", {})
                game_data["ticket_link"] = ticket_info.get("url", "") if ticket_info and ticket_info.get("url") else None
                
                # skip for now
                game_data["box_score"] = None
                game_data["score_breakdown"] = None
                
                process_game_data(game_data)

def process_game_data(game_data):
    """
    Process the game data and store it in the database.

    Args:
        game_data (dict): A dictionary containing the game data.
    """
    
    game_data = normalize_game_data(game_data)
    location_data = game_data["location"].split("\n")
    geo_location = location_data[0]
    if (",") not in geo_location:
        city = geo_location
        state = geo_location
    else:
        parts = [part.strip() for part in geo_location.split(",")]
        city = parts[0]
        state = parts[-1]
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

    # ISO format
    utc_date_str = game_data["utc_date"].isoformat() if game_data["utc_date"] else None

    game_time = game_data["time"]
    if game_time is None:
        game_time = "TBD"

    is_home_game = "Ithaca" in city
    
    # make sure cornell is first in score breakdown - switch order on home games
    # do this before branching
    if game_data["score_breakdown"] and is_home_game:
        game_data["score_breakdown"] = game_data["score_breakdown"][::-1]

    # consistency check for ice hockey, since can be randomly ordered
    if game_data["sport"] == "Ice Hockey" and game_data["score_breakdown"] and game_data["box_score"]:
        # Get final scores from box score
        final_box_cor_score = None
        final_box_opp_score = None
        for event in reversed(game_data["box_score"]):
            if "cor_score" in event and "opp_score" in event:
                final_box_cor_score = event["cor_score"]
                final_box_opp_score = event["opp_score"]
                break
        
        # Compare with score breakdown
        if final_box_cor_score and len(game_data["score_breakdown"]) >= 2:
            cor_final = game_data["score_breakdown"][0][-1]
            opp_final = game_data["score_breakdown"][1][-1]
            
            # If they don't match, flip the arrays
            if str(final_box_cor_score) != str(cor_final) or str(final_box_opp_score) != str(opp_final):
                game_data["score_breakdown"] = game_data["score_breakdown"][::-1]

    # Try to find by tournament key fields to handle placeholder teams
    curr_game = GameService.get_game_by_tournament_key_fields(
        city,
        game_data["date"],
        game_data["gender"],
        location,
        game_data["sport"],
        state
    )
    
    # If no tournament game found, try the regular lookup with opponent_id
    if not curr_game:
        curr_game = GameService.get_game_by_key_fields(
            city,
            game_data["date"],
            game_data["gender"],
            location,
            team.id,
            game_data["sport"],
            state
        )

    if isinstance(curr_game, list):
        if curr_game:
            curr_game = curr_game[0]
        else:
            curr_game = None
    if curr_game:
        updates = {
            "time": game_time,
            "result": game_data["result"],
            "box_score": game_data["box_score"],
            "score_breakdown": game_data["score_breakdown"],
            "utc_date": utc_date_str,
            "city": city,
            "location": location,
            "state": state,
            "ticket_link": game_data["ticket_link"]
        }
        
        current_team = TeamService.get_team_by_id(curr_game.opponent_id)
        if current_team and is_tournament_placeholder_team(current_team.name):
            updates["opponent_id"] = team.id
            
            if is_cornell_loss(game_data["result"]) and game_data["utc_date"]:
                GameService.handle_tournament_loss(game_data["sport"], game_data["gender"], game_data["utc_date"])
                        
        GameService.update_game(curr_game.id, updates)
        return
        
    game_data = {
        "city": city,
        "date": game_data["date"],
        "gender": game_data["gender"],
        "location": location,
        "opponent_id": team.id,
        "result": game_data["result"],
        "sport": game_data["sport"],
        "state": state,
        "time": game_time,
        "box_score": game_data["box_score"],
        "score_breakdown": game_data["score_breakdown"],
        "utc_date": utc_date_str,
        "ticket_link": game_data["ticket_link"]
    }

    GameService.create_game(game_data)