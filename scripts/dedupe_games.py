"""
Remove duplicate games that differ only in how their state was written.

The old scraper took the state straight from the page, which spelled the same
state several ways ("MD" and "Md.", "N.Y." and "NY"), so the same game could be
stored twice. Canonicalizing the state makes those rows identical, which also
makes them collide with the unique index on
(sport, gender, date, opponent_id, state).

For each colliding group this keeps one row and deletes the rest. The keeper is
chosen by how much it carries, not arbitrarily: a row with an event_id wins,
then one with a box score, then one with a result, then the oldest.

    python3 scripts/dedupe_games.py             # dry run, deletes nothing
    python3 scripts/dedupe_games.py --apply
"""

import argparse
import collections
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db  # noqa: E402
from src.scrapers.games_scraper import normalize_state  # noqa: E402


def keep_score(game):
    """How much a row is worth keeping. Higher wins."""
    return (
        1 if game.get("event_id") else 0,
        1 if game.get("box_score") else 0,
        1 if game.get("score_breakdown") else 0,
        1 if game.get("result") else 0,
        1 if game.get("recap_link") else 0,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="delete the duplicates (default is a dry run)")
    args = parser.parse_args()

    collection = db["game"]
    groups = collections.defaultdict(list)

    for game in collection.find():
        key = (
            game.get("sport"),
            game.get("gender"),
            game.get("date"),
            game.get("opponent_id"),
            normalize_state(game.get("state")),
        )
        groups[key].append(game)

    duplicates = {key: rows for key, rows in groups.items() if len(rows) > 1}
    to_delete = []

    print(f"=== {collection.count_documents({})} game(s), {len(duplicates)} duplicate group(s) ===\n")

    for key, rows in duplicates.items():
        ranked = sorted(rows, key=keep_score, reverse=True)
        keeper, losers = ranked[0], ranked[1:]
        to_delete.extend(losers)

        print(f"  {key[0]} {key[1]} {key[2]} (state -> {key[4]})")
        print(f"    KEEP   _id={keeper['_id']} state={keeper.get('state')!r} "
              f"event_id={keeper.get('event_id')} box_score={bool(keeper.get('box_score'))}")
        for loser in losers:
            print(f"    DELETE _id={loser['_id']} state={loser.get('state')!r} "
                  f"event_id={loser.get('event_id')} box_score={bool(loser.get('box_score'))}")

    print(f"\n  rows to delete: {len(to_delete)}")

    if not to_delete:
        print("\nNothing to do.")
        return

    if args.apply:
        result = collection.delete_many({"_id": {"$in": [row["_id"] for row in to_delete]}})
        print(f"\nDeleted {result.deleted_count} duplicate game(s).")
        print(f"Remaining: {collection.count_documents({})}")
    else:
        print("\nDry run, nothing deleted. Re-run with --apply.")


if __name__ == "__main__":
    main()
