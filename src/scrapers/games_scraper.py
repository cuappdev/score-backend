from dotenv import load_dotenv

load_dotenv()

import requests
from src.utils.convert_to_utc import convert_to_utc, parse_time_string
from src.utils.constants import *
from src.scrapers.game_details_scrape import scrape_game, scrape_sidearm_story_recap
from src.utils.helpers import (
    DB_DATE_FORMAT,
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
from datetime import timedelta, datetime, timezone
import pytz

# The calendar feed reports event dates and times in Cornell's local timezone.
EASTERN_TZ = pytz.timezone("US/Eastern")

logger = logging.getLogger(__name__)
RECAP_FIELDS = ["recap_article_title", "recap_article_image", "recap_published_at"]


def eastern_today():
    """
    Today's date in Cornell's timezone. The calendar feed labels events in
    Eastern time, so comparing against the server's local date is wrong whenever
    the two disagree: in a UTC container (see Dockerfile) anything after 8pm
    Eastern already reads as tomorrow, which would skip evening games while they
    are being played.
    """
    return datetime.now(EASTERN_TZ).date()


def is_date_today(date_str):
    """
    Returns True if the given ISO date string (e.g. "2025-12-28T00:00:00")
    is the current date in Eastern time. Compares only year, month, day.
    """
    if not date_str:
        return False
    try:
        date_clean = date_str.split(".")[0].replace("Z", "")
        event_date = datetime.strptime(date_clean, "%Y-%m-%dT%H:%M:%S").date()
        return event_date == eastern_today()
    except (ValueError, TypeError):
        return False


def is_match_time_passed(time_str):
    """
    Returns True if the current time is past the given time (today).
    time_str: e.g. "4:00 p.m." — assumes today's date.
    """
    if not time_str:
        return False

    # convert_to_utc falls back to midnight when it cannot read a clock value,
    # which would make "TBA", "TBD" and "All Day" look started from midnight on.
    # Require a real time before comparing.
    if parse_time_string(time_str) is None:
        return False

    today_str = eastern_today().strftime("%b %d %Y")
    match_utc = convert_to_utc(today_str, time_str)
    if match_utc is None:
        return False
    return datetime.now(timezone.utc) >= match_utc
def _recap(recap_link):
    if not recap_link:
        return {field: None for field in RECAP_FIELDS} | {"success": True}
    recap = scrape_sidearm_story_recap(recap_link)
    if not recap or not any(recap.get(field) for field in RECAP_FIELDS):
        return {field: None for field in RECAP_FIELDS} | {"success": False}
    return recap | {"success": True}

def get_n_weeks_before_and_after_from_today(n):
    """
    Week-start dates covering n weeks either side of today, today included.

    Each fetch returns the seven days beginning at the date requested, so the
    steps have to start at -n weeks and run through +n with no gaps. Counting
    outward from 7 skipped today's own week, which is the one that matters most.
    """
    today = eastern_today()
    return [
        (today + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(-n * 7, (n + 1) * 7, 7)
    ]

def fetch_game_schedule():
    """
    Scrape the game schedule from the given URLs in parallel using threads.
    Each sport is scraped in its own thread for improved performance.
    """
    dates = get_n_weeks_before_and_after_from_today(2)

    threads = []
    for date in dates:
        thread = threading.Thread(
            target=parse_calendar_data,
            args=(date,),
            name=f"Scraper-Calendar-{date}"
        )

        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

def normalize_state(value):
    """
    Reduce a state to a canonical two-letter form.

    The feed writes the same state several ways ("N.Y.", "NY", "Conn.", "CT"),
    and city/state is part of how a game is looked up, so without this the same
    venue matches as two different places.
    """
    if not value:
        return None

    letters = re.sub(r"[^A-Za-z]", "", str(value)).upper()
    if not letters:
        return None
    if len(letters) == 2:
        return letters
    return STATE_ABBREVIATIONS.get(letters, str(value).strip())


def split_event_location(location):
    """
    Split the feed's "City, ST" into (city, state), with the state canonicalized.

    Some entries carry no comma at all, in which case the whole string is used
    for both, matching what the old schedule parser did.
    """
    text = normalize_placeholder(location)
    if not text or text == "TBA":
        return "TBA", "TBA"

    if "," in text:
        city, state = [part.strip() for part in text.split(",", 1)]
    else:
        city = state = text.strip()
    return normalize_placeholder(city), normalize_state(state)


def build_result(result):
    """
    Render the feed's result object the way the schedule page wrote it, e.g.
    "W,99-59". Returns None for a game that has not been played.
    """
    if not result:
        return None

    status = result.get("status")
    team_score = result.get("team_score")
    opponent_score = result.get("opponent_score")

    # "N" means no result yet and an unplayed game carries null scores
    if not status or status == "N" or team_score is None or opponent_score is None:
        return None
    return f"{status},{team_score}-{opponent_score}"


def opponent_logo_url(opponent):
    """Absolute URL for the opponent's logo, or None when the feed has none."""
    image = (opponent or {}).get("image") or {}
    path, filename = image.get("path"), image.get("filename")
    if not path or not filename:
        return None
    return safe_absolute_url(f"{path.rstrip('/')}/{filename}")


def calendar_event_to_game_data(event):
    """
    Convert one calendar event into the shape process_game_data expects.

    Returns None for an event we cannot place, which currently means a sport
    whose code is not in SIDEARM_SPORTS.
    """
    sport_info = SIDEARM_SPORTS.get((event.get("sport") or {}).get("global_sport_shortname"))
    if not sport_info:
        logger.warning(
            "Skipping event %s: unknown sport code %r",
            event.get("id"),
            (event.get("sport") or {}).get("global_sport_shortname"),
        )
        return None

    opponent = event.get("opponent") or {}
    media = event.get("media") or {}
    facility = event.get("facility") or {}
    result = event.get("result") or {}

    # The feed's date is ISO; the stored format is "Nov 8 (Sun) 2026".
    utc_date = None
    date_text = None
    raw_date = event.get("date")
    if raw_date:
        try:
            parsed = datetime.strptime(raw_date.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            date_text = parsed.strftime(DB_DATE_FORMAT).replace(" 0", " ")
            utc_date = EASTERN_TZ.localize(parsed).astimezone(timezone.utc)
        except (ValueError, TypeError):
            logger.warning("Skipping event %s: unparseable date %r", event.get("id"), raw_date)
            return None

    city, state = split_event_location(event.get("location"))

    return {
        "event_id": event.get("id"),
        "sport": sport_info["sport"],
        "gender": sport_info["gender"],
        "opponent_name": normalize_placeholder(opponent.get("title")),
        "opponent_logo": opponent_logo_url(opponent),
        "date": date_text,
        "utc_date": utc_date,
        "time": normalize_placeholder(event.get("time")),
        "city": city,
        "state": state,
        # The feed keeps the venue separate from the city, it is absent for away games at a site Cornell does not track
        "location": normalize_placeholder(facility.get("title")),
        "result": build_result(result),
        "ticket_link": ((media.get("tickets") or {}).get("url")),
        "recap_link": ((result.get("recap") or {}).get("url")),
        "box_score_link": ((result.get("boxscore") or {}).get("url")),
    }


def parse_calendar_data(date):
    """
    Parse the game schedule page and store the data in the database.
    Args:
        url (str): The URL of the game schedule page.
        sport (str): The sport of the games.
        gender (str): The gender of the games.
    """
    url = f"{CALENDAR_URL}&date={date}T00:00:00"
    try:
        response = requests.get(url, headers=HTTP_REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Unable to fetch schedule %s: %s", url, exc)
        return

    try:
        events_data = response.json()
    except ValueError as exc:
        logger.warning("Calendar feed at %s was not JSON: %s", url, exc)
        return

    # A multi-day event is listed under every day it spans, so the same event
    # arrives several times in one response. Keep one of each.
    # The feed also sends "events": null for an empty day, so a get() default
    # never fires: the key is present, its value is just None.
    events = {}
    for day in events_data or []:
        for event in day.get("events") or []:
            events.setdefault(event.get("id"), event)

    for event in events.values():
        game_data = calendar_event_to_game_data(event)
        if not game_data:
            continue
        try:
            process_game_data(game_data)
        except Exception as exc:
            # One malformed event should not cost the rest of the week.
            logger.error(
                "Failed to process calendar event %s: %s",
                event.get("id"),
                exc,
                exc_info=True,
            )


def as_game_list(result):
    """
    Normalize a lookup result, which may be a single game, a list, or None,
    into a list.
    """
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [result]


def narrow_by_time(candidates, game_time):
    """
    Reduce several matching games to the one being processed.

    Returns (game, ambiguous). A caller that gets ambiguous=True must not guess:
    these lookups deliberately ignore opponent_id, so picking arbitrarily is how
    one game ends up overwriting another on a doubleheader.
    """
    if not candidates:
        return None, False
    if len(candidates) == 1:
        return candidates[0], False

    if game_time:
        timed = [game for game in candidates if game.time == game_time]
        if len(timed) == 1:
            return timed[0], False

    return None, True


def is_placeholder_game(game):
    """True if the game's opponent is still a tournament placeholder."""
    # Imported here for the same reason process_game_data does: src.services
    # pulls in the database layer, which must not load at module import time.
    from src.services import TeamService

    team = TeamService.get_team_by_id(game.opponent_id)
    return bool(team and is_tournament_placeholder_team(team.name))

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


def build_game_updates(game_data, team, city, state, location, game_time, utc_date_str):
    """
    The fields we write on every match, however the game was found.

    _detail_updates only contributes box_score/score_breakdown and the recap
    fields when their scrape actually succeeded, so a failed scrape leaves the
    stored values alone instead of overwriting them with None.
    """
    return {
        "time": game_time,
        "result": game_data["result"],
        "utc_date": utc_date_str,
        "city": city,
        "location": location,
        "state": state,
        "opponent_id": team.id,
        "ticket_link": game_data["ticket_link"],
        # Stamp the id on rows that predate it, so the next run takes the fast path.
        "event_id": game_data.get("event_id"),
        **_detail_updates(game_data),
    }


def process_game_data(game_data):
    """
    Process the game data and store it in the database.

    Args:
        game_data (dict): A dictionary containing the data for a game.
    """
    from src.services import GameService, TeamService

    # The calendar carries links but no play data, so the box score and recap are separate fetches

    box_score_link = safe_absolute_url(game_data.get("box_score_link"))
    game_data["_box_score_scrape_succeeded"] = False

    if box_score_link:
        try:
            details = scrape_game(box_score_link, game_data["sport"].lower())
        except Exception as exc:
            logger.warning("Unable to scrape box score %s: %s", box_score_link, exc)
            details = None

        if not isinstance(details, dict) or details.get("error"):
            if isinstance(details, dict) and details.get("error"):
                logger.warning(
                    "Box score scrape failed for %s: %s", box_score_link, details["error"]
                )
        else:
            game_data["_box_score_scrape_succeeded"] = True
            game_data["box_score"] = details.get("scoring_summary")
            game_data["score_breakdown"] = details.get("scores")

            # These sports list the home team first, so swap to keep Cornell in the first column for home games
            if game_data["sport"] in ("Baseball", "Football", "Lacrosse"):
                if "Ithaca" in (game_data.get("city") or "") and game_data.get("box_score"):
                    for event in game_data["box_score"]:
                        if "cor_score" in event and "opp_score" in event:
                            event["cor_score"], event["opp_score"] = (
                                event["opp_score"],
                                event["cor_score"],
                            )

    recap_link = safe_absolute_url(game_data.get("recap_link"))
    game_data["_recap_scrape_succeeded"] = False
    if recap_link:
        game_data["recap_link"] = recap_link
        recap = _recap(recap_link)
        game_data["_recap_scrape_succeeded"] = recap.pop("success", False)
        game_data.update(recap)

    # calendar_event_to_game_data has already split city, state and venue and
    # canonicalized the state, so take them as given.
    city = game_data.get("city")
    state = game_data.get("state")
    location = game_data.get("location")

    game_data = normalize_game_data(game_data)

    if game_data.get("opponent_logo") and not is_allowed_url(game_data["opponent_logo"]):
        logger.warning("Skipping unapproved opponent logo URL: %s", game_data["opponent_logo"])
        game_data["opponent_logo"] = None

    team = TeamService.get_team_by_name(game_data.get("opponent_name"))
    if not team:
        logo_url = game_data.get("opponent").get("website")+game_data.get("opponent").get("image").get("filename")
        color = (
            get_dominant_color(logo_url)
            if logo_url
            else "#FFFFFF"
        )
        encoded_opponent_logo = ""
        if logo_url:
            try:
                response = requests.get(logo_url, headers=HTTP_REQUEST_HEADERS, timeout=30)
                response.raise_for_status()
                encoded_opponent_logo = base64.b64encode(response.content).decode('utf-8')
            except Exception as e:
                print(f"Error fetching encoded opponent logo: {e}")
        team_data = {
            "color": color,
            "image": logo_url,
            "b64_image": encoded_opponent_logo,
            "name": game_data.get("opponent").get("title"),
        }
        team = TeamService.create_team(team_data)

    # ISO format
    utc_date_obj = game_data["utc_date"]
    utc_date_str = utc_date_obj.isoformat() if hasattr(utc_date_obj, "isoformat") else utc_date_obj

    game_time = normalize_placeholder(game_data.get("time"))
    is_home_game = "Ithaca" in city
    
    # make sure cornell is first in score breakdown - switch order on home games
    # do this before branching
    if game_data.get("score_breakdown") and is_home_game:
        game_data["score_breakdown"] = game_data.get("score_breakdown")[::-1]

    # consistency check for ice hockey, since can be randomly ordered
    if game_data["sport"] == "Ice Hockey" and game_data.get("score_breakdown") and game_data.get("box_score"):
        # Get final scores from box score
        final_box_cor_score = None
        final_box_opp_score = None
        for event in reversed(game_data.get("box_score")):
            if "cor_score" in event and "opp_score" in event:
                final_box_cor_score = event["cor_score"]
                final_box_opp_score = event["opp_score"]
                break
        
        # Compare with score breakdown
        if final_box_cor_score is not None and len(game_data.get("score_breakdown")) >= 2:
            cor_final = game_data.get("score_breakdown")[0][-1]
            opp_final = game_data.get("score_breakdown")[1][-1]
            
            # If they don't match, flip the arrays
            if str(final_box_cor_score) != str(cor_final) or str(final_box_opp_score) != str(opp_final):
                game_data["score_breakdown"] = game_data.get("score_breakdown")[::-1]

    event_id = game_data.get("event_id")
    curr_game = GameService.get_game_by_event_id(event_id) if event_id else None

    if curr_game:
        updates = build_game_updates(game_data, team, city, state, location, game_time, utc_date_str)
        current_team = TeamService.get_team_by_id(curr_game.opponent_id)
        if current_team and is_tournament_placeholder_team(current_team.name):
            if is_cornell_loss(game_data["result"]) and utc_date_obj:
                GameService.handle_tournament_loss(game_data["sport"], game_data["gender"], utc_date_obj)
        GameService.update_game(curr_game.id, updates)
        return curr_game.id

    # This lookup ignores opponent_id so a row still holding a placeholder can be
    # claimed by the real opponent. Filter to placeholders before choosing, or a
    # real game returned first would mask a placeholder behind it and we would
    # create a duplicate instead of filling the placeholder in.
    tournament_matches = [
        game
        for game in as_game_list(
            GameService.get_game_by_tournament_key_fields(
                city,
                game_data["date"],
                game_data["gender"],
                location,
                game_data["sport"],
                state,
            )
        )
        if is_placeholder_game(game)
    ]

    curr_game, ambiguous = narrow_by_time(tournament_matches, game_time)
    if ambiguous:
        logger.warning(
            "Skipping %s %s on %s at %s: %s placeholder games match and the time "
            "%r does not single one out",
            game_data["gender"],
            game_data["sport"],
            game_data["date"],
            city,
            len(tournament_matches),
            game_time,
        )
        return None

    # If no placeholder matched, look the game up by its actual opponent.
    if not curr_game:
        key_matches = as_game_list(
            GameService.get_game_by_key_fields(
                city,
                game_data["date"],
                game_data["gender"],
                location,
                team.id,
                game_data["sport"],
                state,
            )
        )
        curr_game, ambiguous = narrow_by_time(key_matches, game_time)
        if ambiguous:
            logger.warning(
                "Skipping %s %s vs %s on %s: %s games match and the time %r does "
                "not single one out",
                game_data["gender"],
                game_data["sport"],
                game_data["opponent_name"],
                game_data["date"],
                len(key_matches),
                game_time,
            )
            return None

    updates = build_game_updates(game_data, team, city, state, location, game_time, utc_date_str)

    if curr_game:
        current_team = TeamService.get_team_by_id(curr_game.opponent_id)
        if current_team and is_tournament_placeholder_team(current_team.name):
            if is_cornell_loss(game_data["result"]) and utc_date_obj:
                GameService.handle_tournament_loss(game_data["sport"], game_data["gender"], utc_date_obj)
        GameService.update_game(curr_game.id, updates)
        return curr_game.id

    create_data = {
        **updates,
        "date": game_data["date"],
        "gender": game_data["gender"],
        "sport": game_data["sport"],
        "box_score": updates.get("box_score"),
        "score_breakdown": updates.get("score_breakdown"),
        "recap_link": game_data.get("recap_link"),
        "recap_article_title": updates.get("recap_article_title"),
        "recap_article_image": updates.get("recap_article_image"),
        "recap_published_at": updates.get("recap_published_at"),
    }

    created = GameService.create_game(create_data)
    return created.id if created else None

def get_live_games(data):
    """
    Get live games from the given data.
    """
    today = next((day for day in data or [] if is_date_today(day.get("date", ""))), None)
    if not today:
        return []

    # The feed sends "events": null for a day with nothing scheduled, so the
    # get() default never fires - the key is present, its value is just None.
    today_games = today.get("events") or []
    return [game for game in today_games if is_match_time_passed(game.get("time", ""))]

def fetch_live_games():
    """
    Fetch live games and apply them.

    Runs inline rather than spawning a thread: APScheduler already executes the
    job on its own worker, and its default max_instances=1 then means a cycle
    that overruns the 30s interval is skipped instead of piling up overlapping
    scrapes that duplicate each other's work.
    """
    parse_live_page(LIVE_PREFIX)

def parse_live_page(url):
    from src.services import GameService

    # Eastern, like the rest of the live path: near midnight UTC the server's
    # own date can be a day ahead, which would request the wrong feed week.
    today = eastern_today()
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
        **HTTP_REQUEST_HEADERS,
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
        try:
            GameService.update_live_game(game)
        except Exception as e:
            # Keep going: one bad feed should not cost every other live game
            # its update for this cycle.
            logger.error(
                "Failed to update live game %s (%s): %s",
                game.get("id"),
                stats_url or "no stats url",
                e,
                exc_info=True,
            )
