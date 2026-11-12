"""
Run the real schedule scraper without writing to the database.

Every create and update is intercepted and summarised, so the write volume and
the update/create split can be checked before the scraper is let loose on real
data. A run that creates far more than it updates means matching is failing.

    python3 scripts/dry_run_scraper.py            # the window the scheduler uses
    python3 scripts/dry_run_scraper.py 2026-11-08 # specific week start(s)
"""

import collections
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import GameService  # noqa: E402
import src.scrapers.games_scraper as scraper  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

counts = collections.Counter()
creates, updates = [], []

GameService.update_game = staticmethod(
    lambda game_id, data: (counts.update(["update"]), updates.append(data))
)
GameService.create_game = staticmethod(
    lambda data: (counts.update(["create"]), creates.append(data), None)[-1]
)
# Teams are created as a side effect of an unseen opponent; count without writing.
_real_create_team = GameService and None
from src.services import TeamService  # noqa: E402
TeamService.create_team = staticmethod(
    lambda data: (counts.update(["team_created"]), type("T", (), {"id": "dry-run"})())[-1]
)

dates = sys.argv[1:] or scraper.get_n_weeks_before_and_after_from_today(2)
print(f"Dry run over {len(dates)} week(s): {dates}\n")

for date in dates:
    scraper.parse_calendar_data(date)

total = counts["update"] + counts["create"]
print(f"\n=== {total} write(s) ===")
print(f"  updates:        {counts['update']}")
print(f"  creates:        {counts['create']}")
print(f"  teams created:  {counts['team_created']}")
print(f"  with event_id:  {sum(1 for d in updates + creates if d.get('event_id'))}/{total}")
print(f"  with box_score: {sum(1 for d in updates + creates if d.get('box_score'))}")

if creates:
    print(f"\n  CREATES ({len(creates)}) - each is a game not already stored:")
    for d in creates[:15]:
        print(f"    event_id={d.get('event_id')} {d.get('sport')} {d.get('gender')} "
              f"{d.get('date')} {d.get('time')} vs opponent_id={d.get('opponent_id')}")
    if len(creates) > 15:
        print(f"    ... and {len(creates) - 15} more")

print("\nNothing was written. Inspect the creates above: a large number means matching is failing.")
