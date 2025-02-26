import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from src.services import GameService, TeamService
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game
from src.utils.helpers import get_dominant_color
import base64
import html

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
        
        game_year = infer_game_year(date_text, season_years)
        if date_text and game_year:
            game_data["date"] = f"{date_text} {game_year}"
        else:
            game_data["date"] = date_text

        game_data["time"] = time_tag.text.strip() if time_tag else None

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
        if curr_game.result != game_data["result"]:
            GameService.update_game(curr_game.id, {"result": game_data["result"]})
        if curr_game.box_score != game_data["box_score"]:
            GameService.update_game(curr_game.id, {"box_score": game_data["box_score"]})
            GameService.update_game(curr_game.id, {"score_breakdown": game_data["score_breakdown"]})
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
        "time": game_data["time"],
        "box_score": game_data["box_score"],
        "score_breakdown": game_data["score_breakdown"]
    }

    GameService.create_game(game_data)