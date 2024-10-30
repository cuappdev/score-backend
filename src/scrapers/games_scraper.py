import requests
from bs4 import BeautifulSoup
from src.services import GameService, TeamService
from src.utils.constants import *


def scrape_game_schedule(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    games = []

    for game_item in soup.select(GAME_TAG):
        game_data = {}

        opponent_name_tag = game_item.select_one(OPPONENT_NAME_TAG)
        opponent_name = opponent_name_tag.text.strip() if opponent_name_tag else None
        game_data["opponent_name"] = opponent_name

        opponent_logo_tag = game_item.select_one(OPPONENT_LOGO_TAG)
        opponent_logo = (
            opponent_logo_tag[OPPONENT_LOGO_URL_ATTR] if opponent_logo_tag else None
        )
        game_data["opponent_logo"] = IMAGE_PREFIX + opponent_logo

        date_tag = game_item.select_one(DATE_TAG)
        time_tag = game_item.select_one(TIME_TAG)
        game_data["date"] = date_tag.text.strip() if date_tag else None
        game_data["time"] = time_tag.text.strip() if time_tag else None

        location_tag = game_item.select_one(LOCATION_TAG)
        game_data["location"] = location_tag.text.strip() if location_tag else None

        process_game_data(game_data)


def process_game_data(game_data):
    location_data = game_data["location"].split("\n")
    location = location_data[0]
    city, state = map(str.strip, location.split(","))

    team = TeamService.get_team_by_name(game_data["opponent_name"])
    if not team:
        team_data = {
            "color": "#000000",
            "image": game_data["opponent_logo"],
            "name": game_data["opponent_name"],
        }
        team = TeamService.create_team(team_data)

    game_data = {
        "city": city,
        "date": game_data["date"],
        "gender": "Men",
        "location": location_data[1] if len(location_data) > 1 else None,
        "opponent_id": team.id,
        "sport": "Basketball",
        "state": state,
        "time": game_data["time"],
    }

    GameService.create_game(game_data)


url = SCHEDULE_PREFIX + SPORTS + SCHEDULE_POSTFIX
scrape_game_schedule(url)

# if __name__ == "__main__":
#     url = "https://cornellbigred.com/sports/mens-basketball/schedule"
#     scrape_game_schedule(url)
