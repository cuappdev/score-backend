"""
Backfill `event_id` on stored games from Sidearm's calendar feed.

Games were matched on date, sport, gender, city and state, which cannot tell
two games on the same day at the same venue apart. The calendar feed gives each
game a stable id, which identifies it exactly. This assigns that id to the games
already in the database, so the scraper can switch to matching on it without
re-creating every row it has already stored.

Run this BEFORE the scraper starts matching on event_id. Until a game has its
id, the scraper falls back to field matching and would create a duplicate.

Matching is deliberately conservative: a feed event is only assigned to a stored
game when exactly one game matches, first on date/sport/gender/time and then,
where several match, narrowed by opponent. Anything still ambiguous is reported
and left alone rather than guessed at.

    python3 scripts/backfill_event_id.py             # dry run, writes nothing
    python3 scripts/backfill_event_id.py --apply
    python3 scripts/backfill_event_id.py --weeks 40  # widen the feed sweep
"""

import argparse
import datetime
import os
import sys
from collections import defaultdict

import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db  # noqa: E402
from src.scrapers.games_scraper import calendar_event_to_game_data  # noqa: E402
from src.services import TeamService  # noqa: E402
from src.utils.convert_to_utc import parse_time_string  # noqa: E402
from src.utils.constants import CALENDAR_URL, HTTP_REQUEST_HEADERS  # noqa: E402
from src.utils.helpers import DB_DATE_FORMAT  # noqa: E402

# How far back to sweep regardless of what is stored. The feed happily serves
# 2024, and stored games reach back to early 2025.
EARLIEST_SWEEP = datetime.date(2024, 8, 1)


def stored_date_range():
    """
    The span of dates already in the database.

    The sweep is driven by this rather than a fixed season, because stored
    games reach back further than the current year and the feed serves past
    seasons just as happily as future ones.
    """
    dates = []
    for game in db["game"].find({}, {"date": 1}):
        try:
            dates.append(datetime.datetime.strptime(game["date"].strip(), DB_DATE_FORMAT).date())
        except (ValueError, TypeError, AttributeError, KeyError):
            continue
    if not dates:
        today = datetime.date.today()
        return today, today

    # Reach back past the earliest stored game: the feed serves older seasons,
    # and games from before our first stored row can still turn up.
    return min(min(dates), EARLIEST_SWEEP), max(dates)


def fetch_events(start, end):
    """
    Every event the feed knows about between two dates, by id.

    The feed answers a week at a time, so this walks the range in weekly steps.
    Windows overlap, which is harmless: an id seen twice is the same event.
    """
    events = {}
    day = start
    while day <= end:
        try:
            response = requests.get(
                CALENDAR_URL,
                params={"date": day.strftime("%Y-%m-%dT00:00:00")},
                headers=HTTP_REQUEST_HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            print(f"  (skipping week of {day}: {error})")
            payload = []

        for entry in payload or []:
            # The feed sends "events": null for a day with nothing scheduled.
            for event in entry.get("events") or []:
                if event.get("id") is not None:
                    events[event["id"]] = event

        day += datetime.timedelta(days=7)

    return events


def find_stored_game(collection, mapped):
    """
    The one stored game this event refers to.

    Returns (game, reason). game is None when nothing matches or when more than
    one does, with the reason naming which.
    """
    base = {
        "date": mapped["date"],
        "sport": mapped["sport"],
        "gender": mapped["gender"],
    }
    projection = {"_id": 1, "opponent_id": 1, "event_id": 1, "time": 1}
    candidates = list(collection.find({**base, "time": mapped["time"]}, projection))

    if not candidates:
        # The old scraper sometimes wrote a date or a placeholder into the time
        # column for multi-day events ("Sep 27 (Sun)", "All Day", "TBD"), so
        # those rows can never match on time. Fall back to the day's games for
        # this team and let the opponent separate them.
        candidates = [
            row
            for row in collection.find(base, projection)
            if parse_time_string(row.get("time")) is None
        ]

    if not candidates:
        return None, "no stored game"

    if len(candidates) > 1:
        # Several games share the slot, which happens for tournaments. The
        # opponent usually separates them.
        team = TeamService.get_team_by_name(mapped["opponent_name"])
        if team:
            narrowed = [c for c in candidates if c.get("opponent_id") == team.id]
            if narrowed:
                candidates = narrowed

    if len(candidates) > 1:
        return None, f"ambiguous ({len(candidates)} stored games match)"

    return candidates[0], "matched"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    parser.add_argument("--start", help="first date to sweep, YYYY-MM-DD (default: earliest stored game)")
    parser.add_argument("--end", help="last date to sweep, YYYY-MM-DD (default: latest stored game)")
    args = parser.parse_args()

    start, end = stored_date_range()
    if args.start:
        start = datetime.datetime.strptime(args.start, "%Y-%m-%d").date()
    if args.end:
        end = datetime.datetime.strptime(args.end, "%Y-%m-%d").date()

    weeks = (end - start).days // 7 + 1
    print(f"Sweeping the calendar feed from {start} to {end} ({weeks} request(s))...")
    events = fetch_events(start, end)
    print(f"  feed returned {len(events)} distinct event(s)\n")

    collection = db["game"]
    updates, already, new_games, ambiguous = [], 0, [], []
    claims = defaultdict(list)

    for event_id, event in sorted(events.items()):
        mapped = calendar_event_to_game_data(event)
        if not mapped:
            continue

        game, reason = find_stored_game(collection, mapped)

        if game is None:
            (new_games if reason == "no stored game" else ambiguous).append((mapped, reason))
            continue

        if game.get("event_id") == event_id:
            already += 1
            continue

        claims[game["_id"]].append((event_id, mapped))

    # Two feed events can resolve to the same stored game when the day holds several events we only ever stored once (back-to-back sailing regattas, for instance). Assigning either id would be a guess, so assign neither.
    contested = {gid: c for gid, c in claims.items() if len(c) > 1}
    for gid, claimants in contested.items():
        for event_id, mapped in claimants:
            ambiguous.append(
                (mapped, f"contested (event {event_id} shares one stored game with "
                         f"{len(claimants) - 1} other event(s))")
            )

    for gid, claimants in claims.items():
        if gid in contested:
            continue
        event_id, mapped = claimants[0]
        updates.append((gid, event_id, mapped))

    print(f"=== {collection.count_documents({})} stored game(s) ===")
    print(f"  to assign an event_id: {len(updates)}")
    print(f"  already correct:       {already}")
    print(f"  ambiguous, skipped:    {len(ambiguous)}")
    print(f"  in feed but not stored (new games, scraper will create): {len(new_games)}")

    for mapped, reason in ambiguous:
        print(
            f"    SKIP {reason}: {mapped['sport']} {mapped['gender']} "
            f"{mapped['date']} {mapped['time']} vs {mapped['opponent_name']}"
        )

    for game_id, event_id, mapped in updates[:8]:
        print(f"    {event_id} -> {mapped['sport']} {mapped['gender']} {mapped['date']} {mapped['time']}")
    if len(updates) > 8:
        print(f"    ... and {len(updates) - 8} more")

    print()
    if args.apply:
        for game_id, event_id, _ in updates:
            collection.update_one({"_id": game_id}, {"$set": {"event_id": event_id}})
        print(f"Applied: {len(updates)} game(s) given an event_id.")
        print(
            "Games the feed no longer covers keep matching on their fields, "
            "which is fine because the scraper never sees them."
        )
    else:
        print("Dry run, nothing written. Re-run with --apply to write these changes.")


if __name__ == "__main__":
    main()
