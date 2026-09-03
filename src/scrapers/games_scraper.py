import requests
from bs4 import BeautifulSoup
from src.utils.convert_to_utc import convert_to_utc
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game, scrape_sidearm_story_recap
from src.utils.helpers import get_dominant_color, normalize_game_data, is_tournament_placeholder_team, is_cornell_loss
import base64
import logging
import re
import threading


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


def to_absolute_url(link):
    """Convert relative Cornell links like /news/... to absolute URLs."""
    if not link:
        return None
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return f"{BASE_URL.rstrip('/')}/{link.lstrip('/')}"


def parse_game_links(game_item):
    """
    Parse link info for a schedule item.
    Keep Box Score and Recap links separate because they are different detail
    sources. A schedule row can expose either link or both links.
    """
    box_score_tag = game_item.select_one(BOX_SCORE_TAG)
    recap_tag = game_item.select_one(RECAP_TAG)

    ticket_link_tag = game_item.select_one(GAME_TICKET_LINK)
    return {
        "box_score_link": (
            to_absolute_url(box_score_tag.get("href")) if box_score_tag else None
        ),
        "recap_link": (
            to_absolute_url(recap_tag.get("href")) if recap_tag else None
        ),
        "ticket_link": (
            to_absolute_url(ticket_link_tag.get("href"))
            if ticket_link_tag
            else None
        ),
    }

def fetch_game_schedule():
    """
    Scrape the game schedule from the given URLs in parallel using threads.
    Each sport is scraped in its own thread for improved performance.
    """
    threads = []
    
    for sport_slug, data in SPORT_URLS.items():
        url = SCHEDULE_PREFIX + sport_slug + SCHEDULE_POSTFIX

        # create thread for each sport
        thread = threading.Thread(
            target=parse_schedule_page,
            args=(url, data["sport"], data["gender"]),
            name=f"Scraper-{sport_slug}"
        )
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

def parse_schedule_page(url, sport, gender):
    """
    Parse the game schedule page and store the data in the database.
    Args:
        url (str): The URL of the game schedule page.
        sport (str): The sport of the games.
        gender (str): The gender of the games.
    """
    if sport not in SPORT_DETAIL_MODES:
        logging.warning("Skipping unsupported sport schedule: %s", sport)
        return

    response = requests.get(url, headers=HTTP_REQUEST_HEADERS, timeout=30)
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

        # keep old date field for now
        if date_text and game_year:
            full_date_text = f"{date_text} {game_year}"
            game_data["date"] = full_date_text
            game_data["utc_date"] = convert_to_utc(full_date_text, time_text)
        else:
            game_data["date"] = date_text
            game_data["utc_date"] = None

        game_data["time"] = time_text

        location_tag = game_item.select_one(LOCATION_TAG)
        game_data["location"] = location_tag.text.strip() if location_tag else None

        result_tag = game_item.select_one(RESULT_TAG)
        if result_tag:
            raw = result_tag.get_text(" ", strip=True)
            game_data["result"] = re.sub(r"\s+", " ", raw).strip()
        else:
            game_data["result"] = None
            
        links = parse_game_links(game_item)
        box_score_link = links["box_score_link"]
        recap_link = links["recap_link"]
        detail_mode = SPORT_DETAIL_MODES.get(sport)

        if not detail_mode:
            logging.warning("Skipping unsupported sport: %s", sport)
            continue

        game_data.update({
            "box_score": None,
            "score_breakdown": None,
            "recap_link": recap_link if detail_mode == DETAIL_MODE_RECAP_LINK else None,
            "recap_article_title": None,
            "recap_published_at": None,
            "recap_article_image": None,
        })

        if detail_mode == DETAIL_MODE_BOX_SCORE and box_score_link:
            game_details = scrape_game(box_score_link, sport.lower())
            if not game_details.get("error"):
                game_data["box_score"] = game_details.get("scoring_summary")
                game_data["score_breakdown"] = game_details.get("scores")

                if sport in ["Baseball", "Football", "Lacrosse"]:
                    geo_location = (game_data["location"] or "").split("\n")[0]
                    if "Ithaca" in geo_location and game_data["box_score"]:
                        for event in game_data["box_score"]:
                            if "cor_score" in event and "opp_score" in event:
                                event["cor_score"], event["opp_score"] = (
                                    event["opp_score"],
                                    event["cor_score"],
                                )
        elif detail_mode == DETAIL_MODE_RECAP_LINK and recap_link:
            game_data.update(scrape_sidearm_story_recap(recap_link))

        game_data["ticket_link"] = links["ticket_link"]
        process_game_data(game_data)


def process_game_data(game_data):
    """
    Process the game data and store it in the database.

    Args:
        game_data (dict): A dictionary containing the game data.
    """
    
    from src.services import GameService, TeamService

    game_data = normalize_game_data(game_data)
    location_raw = game_data.get("location") or ""
    location_data = location_raw.split("\n") if location_raw else [""]
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
        state,
        game_time,
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
            state,
            game_time,
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
            "ticket_link": game_data["ticket_link"],
            "recap_link": game_data.get("recap_link"),
            "recap_article_title": game_data.get("recap_article_title"),
            "recap_published_at": game_data.get("recap_published_at"),
            "recap_article_image": game_data.get("recap_article_image"),
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
        "ticket_link": game_data["ticket_link"],
        "recap_link": game_data.get("recap_link"),
        "recap_article_title": game_data.get("recap_article_title"),
        "recap_published_at": game_data.get("recap_published_at"),
        "recap_article_image": game_data.get("recap_article_image"),
    }
    
    GameService.create_game(game_data)
