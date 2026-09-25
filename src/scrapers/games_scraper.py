import requests
from bs4 import BeautifulSoup
from src.utils.convert_to_utc import convert_to_utc
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game, scrape_sidearm_story_recap
from src.utils.helpers import (
    get_dominant_color,
    is_cornell_loss,
    is_allowed_url,
    is_tournament_placeholder_team,
    normalize_game_data,
    normalize_placeholder,
    safe_absolute_url,
    get_with_retries,
)
import base64
import logging
import re
import threading
from datetime import date, timedelta, datetime, timezone
from urllib.parse import urljoin, urlparse


logger = logging.getLogger(__name__)
RECAP_FIELDS = ["recap_article_title", "recap_article_image", "recap_published_at"]


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


def is_date_today(date_str):
    """
    Returns True if the given ISO date string (e.g. "2025-12-28T00:00:00")
    is the current date. Compares only year, month, day; ignores time.
    """
    if not date_str:
        return False
    try:
        date_clean = date_str.split(".")[0].replace("Z", "")
        event_date = datetime.strptime(date_clean, "%Y-%m-%dT%H:%M:%S").date()
        return event_date == date.today()
    except (ValueError, TypeError):
        return False


def is_match_time_passed(time_str):
    """
    Returns True if the current time is past the given time (today).
    time_str: e.g. "4:00 p.m." — assumes today's date.
    """
    if not time_str:
        return False
    today_str = date.today().strftime("%b %d %Y")
    match_utc = convert_to_utc(today_str, time_str)
    if match_utc is None:
        return False
    return datetime.now(timezone.utc) >= match_utc
def absolute_url(link):
    return safe_absolute_url(link)


def parse_game_links(game_item):
    links = {}
    for name, selector in {
        "box_score_link": BOX_SCORE_TAG,
        "recap_link": RECAP_TAG,
        "ticket_link": GAME_TICKET_LINK,
    }.items():
        tag = game_item.select_one(selector)
        href = tag.get("href") if tag else None
        if name == "ticket_link":
            ticket_url = urljoin(BASE_URL, href) if href else None
            if ticket_url and urlparse(ticket_url).scheme.casefold() in ALLOWED_URL_SCHEMES:
                links[name] = ticket_url
            else:
                if ticket_url:
                    logger.warning("Skipping ticket URL with unapproved scheme: %s", ticket_url)
                links[name] = None
        else:
            links[name] = absolute_url(href)
    return links


def parse_schedule_location(location_text):
    if not location_text or str(location_text).strip().casefold() in {"tba", "tbd"}:
        return "TBA", "TBA", "TBA"

    parts = re.split(r"\s*/\s*|\s*\n\s*", str(location_text).strip(), maxsplit=1)
    geo_location = parts[0].strip()
    location = parts[1].strip() if len(parts) > 1 else "TBA"
    if "," in geo_location:
        city, state = [part.strip() for part in geo_location.split(",", 1)]
    else:
        city = state = geo_location
    return tuple(normalize_placeholder(value) for value in (city, state, location))


def parse_schedule_date_and_time(game_item):
    """Read the start date and time without treating an end date as a time.

    Sidearm uses the same date block for single-day and multi-day events. For
    example, a tournament row can contain ``Nov 12``, ``Nov 15`` and ``TBA``
    as separate spans. The old adjacent-sibling selector returned ``Nov 15``
    as the time in that case.
    """
    date_block = game_item.select_one(SCHEDULE_DATE_BLOCK_TAG)
    if not date_block:
        return "", "TBA"

    spans = date_block.find_all("span")
    date_text = spans[0].get_text(" ", strip=True) if spans else ""
    time_tag = next(
        (
            span
            for span in spans[1:]
            if "enddate" not in {name.casefold() for name in span.get("class", [])}
        ),
        None,
    )
    time_text = normalize_placeholder(
        time_tag.get_text(" ", strip=True) if time_tag else None
    )
    return date_text, time_text


def _recap(recap_link):
    if not recap_link:
        return {field: None for field in RECAP_FIELDS} | {"success": True}
    recap = scrape_sidearm_story_recap(recap_link)
    if not recap or not any(recap.get(field) for field in RECAP_FIELDS):
        return {field: None for field in RECAP_FIELDS} | {"success": False}
    return recap | {"success": True}


def fetch_game_schedule():
    """
    Scrape the game schedule from the given URLs in parallel using threads.
    Each sport is scraped in its own thread for improved performance.
    """
    threads = []
    
    for sport, data in SPORT_URLS.items():
        url = SCHEDULE_PREFIX + sport + SCHEDULE_POSTFIX

        # create thread for each sport
        thread = threading.Thread(
            target=parse_schedule_page,
            args=(url, data["sport"], data["gender"]),
            name=f"Scraper-{sport}"
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
    try:
        response = requests.get(url, headers=HTTP_REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Unable to fetch schedule %s: %s", url, exc)
        return

    soup = BeautifulSoup(response.content, "html.parser")

    page_title = soup.title.text.strip() if soup.title else ""
    season_years = extract_season_years(page_title)

    for game_item in soup.select(GAME_TAG):
        game_data = {}
        game_data["gender"] = gender
        game_data["sport"] = sport

        opponent_name_tag = game_item.select_one(OPPONENT_NAME_TAG_A) or game_item.select_one(OPPONENT_NAME_TAG)
        game_data["opponent_name"] = normalize_placeholder(
            opponent_name_tag.text.strip() if opponent_name_tag else None
        )

        opponent_logo_tag = game_item.select_one(OPPONENT_LOGO_TAG)
        opponent_logo = (
            opponent_logo_tag.get(OPPONENT_LOGO_URL_ATTR)
            or opponent_logo_tag.get("src")
            if opponent_logo_tag else None
        )
        game_data["opponent_logo"] = absolute_url(opponent_logo)

        date_text, time_text = parse_schedule_date_and_time(game_item)

        if not date_text:
            logger.warning("Skipping %s row without a date", sport)
            continue

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
        game_data["location"] = location_tag.get_text("\n", strip=True) if location_tag else None

        result_tag = game_item.select_one(RESULT_TAG)
        if result_tag:
            game_data["result"] = result_tag.text.strip().replace("\n", "")
        else:
            game_data["result"] = None

        links = parse_game_links(game_item)
        box_score_link = links["box_score_link"]
        game_data["_box_score_scrape_succeeded"] = False
        if box_score_link:
            try:
                game_details = scrape_game(box_score_link, sport.lower())
            except Exception as exc:
                logger.warning("Unable to scrape box score %s: %s", box_score_link, exc)
                game_details = None

            if not isinstance(game_details, dict) or game_details.get("error"):
                if isinstance(game_details, dict) and game_details.get("error"):
                    logger.warning(
                        "Box score scrape failed for %s: %s",
                        box_score_link,
                        game_details["error"],
                    )
                game_data["box_score"] = None
                game_data["score_breakdown"] = None
            else:
                game_data["_box_score_scrape_succeeded"] = True
                game_data["box_score"] = game_details.get("scoring_summary")
                game_data["score_breakdown"] = game_details.get("scores")

                if sport in ["Baseball", "Football", "Lacrosse"]:
                    location_data = game_data["location"].split("\n") if game_data["location"] else [""]
                    geo_location = location_data[0]
                    is_home_game = "Ithaca" in geo_location

                    if is_home_game and game_data["box_score"]:
                        for event in game_data["box_score"]:
                            if "cor_score" in event and "opp_score" in event:
                                event["cor_score"], event["opp_score"] = event["opp_score"], event["cor_score"]
        else:
            game_data["box_score"] = None
            game_data["score_breakdown"] = None

        recap = _recap(links["recap_link"])
        game_data["recap_link"] = links["recap_link"]
        for field in RECAP_FIELDS:
            game_data[field] = recap[field]
        game_data["_recap_scrape_succeeded"] = recap["success"]

        game_data["ticket_link"] = links["ticket_link"]
        process_game_data(game_data)


def first_or_none(result):
    """
    Normalize a game lookup result, which may be a single game, a list, or None,
    into a single game or None.
    """
    if isinstance(result, list):
        return result[0] if result else None
    return result
def _detail_updates(game_data):
    updates = {}
    if game_data.get("_box_score_scrape_succeeded", "box_score" in game_data):
        updates["box_score"] = game_data.get("box_score")
        updates["score_breakdown"] = game_data.get("score_breakdown")
    if game_data.get("_recap_scrape_succeeded", "recap_link" in game_data):
        updates["recap_link"] = game_data.get("recap_link")
        if game_data.get("recap_link"):
            updates.update({field: game_data.get(field) for field in RECAP_FIELDS if game_data.get(field) is not None})
        else:
            updates.update({field: None for field in RECAP_FIELDS})
    return updates


def process_game_data(game_data):
    """
    Process the game data and store it in the database.

    Args:
        game_data (dict): A dictionary containing the data for a game.
    """
    from src.services import GameService, TeamService

    if "city" in game_data or "state" in game_data:
        city, state, location = game_data.get("city"), game_data.get("state"), game_data.get("location")
    else:
        city, state, location = parse_schedule_location(game_data.get("location"))
    game_data.update(city=city, state=state, location=location)
    game_data = normalize_game_data(game_data)

    if game_data.get("opponent_logo") and not is_allowed_url(game_data["opponent_logo"]):
        logger.warning("Skipping unapproved opponent logo URL: %s", game_data["opponent_logo"])
        game_data["opponent_logo"] = None

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
                response = requests.get(game_data["opponent_logo"], headers=HTTP_REQUEST_HEADERS, timeout=30)
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
    utc_date_obj = game_data["utc_date"]
    utc_date_str = utc_date_obj.isoformat() if hasattr(utc_date_obj, "isoformat") else utc_date_obj

    game_time = normalize_placeholder(game_data.get("time"))
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
        if final_box_cor_score is not None and len(game_data["score_breakdown"]) >= 2:
            cor_final = game_data["score_breakdown"][0][-1]
            opp_final = game_data["score_breakdown"][1][-1]
            
            # If they don't match, flip the arrays
            if str(final_box_cor_score) != str(cor_final) or str(final_box_opp_score) != str(opp_final):
                game_data["score_breakdown"] = game_data["score_breakdown"][::-1]

    curr_game = first_or_none(
        GameService.get_game_by_tournament_key_fields(
            city,
            game_data["date"],
            game_data["gender"],
            location,
            game_data["sport"],
            state
        )
    )

    if curr_game:
        existing_team = TeamService.get_team_by_id(curr_game.opponent_id)
        if not (existing_team and is_tournament_placeholder_team(existing_team.name)):
            curr_game = None

    # If no tournament game found, try the regular lookup with opponent_id
    if not curr_game:
        curr_game = first_or_none(
            GameService.get_game_by_key_fields(
                city,
                game_data["date"],
                game_data["gender"],
                location,
                team.id,
                game_data["sport"],
                state
            )
        )

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

def get_live_games(data):
    """
    Get live games from the given data.
    """
    today_games = [day for day in data if is_date_today(day.get("date", ""))][0].get("events", [])
    return [game for game in today_games if is_match_time_passed(game.get("time", ""))]

def fetch_live_games():
    """
    Fetch live games from the given URLs in parallel using threads.
    Each sport is scraped in its own thread for improved performance.
    """
    url = LIVE_PREFIX

    # create single thread for all sports
    thread = threading.Thread(
        target=parse_live_page,
        args=(url,),
        name=f"Scraper"
    )
    thread.daemon = True
    thread.start()

    # probably should add thread.join for cleanup

def parse_live_page(url):
    from src.services import GameService

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
        "Referer": LIVE_PREFIX,
    }

    url = "https://cornellbigred.com/services/responsive-calendar.ashx"
    r = get_with_retries(url, params=params, headers=headers, timeout=15)
    data = r.json()

    # Keep only days where the date is today (compare date string to current date)
    live_games = get_live_games(data)

    seen_stats_urls = set()
    for game in live_games:
        stats_url = ((game.get("media") or {}).get("stats") or {}).get("url")
        if stats_url:
            if stats_url in seen_stats_urls:
                continue
            seen_stats_urls.add(stats_url)
        GameService.update_live_game(game)
