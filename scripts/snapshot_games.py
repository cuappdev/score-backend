"""
Snapshot the game collection, or diff the current state against a snapshot.

Running the scraper against a populated database mostly produces updates, so
"it ran without crashing" says very little. This captures the collection before
a run and reports exactly what changed after it: which games were added, which
fields were modified, and what the values went from and to.

    python3 scripts/snapshot_games.py before.json           # capture
    python3 scripts/snapshot_games.py before.json --diff     # compare to now
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db  # noqa: E402

# Noisy or derived fields that change on every run without meaning anything.
IGNORED = {"last_updated"}


def capture():
    return {str(g["_id"]): {k: v for k, v in g.items() if k != "_id"}
            for g in db["game"].find()}


def describe(value, limit=58):
    text = json.dumps(value, default=str)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main():
    path = sys.argv[1]
    if "--diff" not in sys.argv:
        snapshot = capture()
        with open(path, "w") as handle:
            json.dump(snapshot, handle, default=str)
        print(f"Captured {len(snapshot)} game(s) to {path}")
        return

    with open(path) as handle:
        before = json.load(handle)
    after = capture()

    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    changed = {}

    for game_id in after:
        if game_id not in before:
            continue
        old, new = before[game_id], after[game_id]
        diffs = {
            field: (old.get(field), new.get(field))
            for field in set(old) | set(new)
            if field not in IGNORED
            and json.dumps(old.get(field), default=str) != json.dumps(new.get(field), default=str)
        }
        if diffs:
            changed[game_id] = diffs

    print(f"=== before: {len(before)} game(s)   after: {len(after)} game(s) ===")
    print(f"  added:   {len(added)}")
    print(f"  removed: {len(removed)}")
    print(f"  changed: {len(changed)}")

    if added:
        print("\n  ADDED:")
        for game_id in added[:10]:
            g = after[game_id]
            print(f"    event_id={g.get('event_id')} {g.get('sport')} {g.get('gender')} "
                  f"{g.get('date')} {g.get('time')}")

    if removed:
        print("\n  REMOVED (unexpected, the scraper should never delete):")
        for game_id in removed[:10]:
            print(f"    {game_id} {before[game_id].get('sport')} {before[game_id].get('date')}")

    if changed:
        field_counts = {}
        for diffs in changed.values():
            for field in diffs:
                field_counts[field] = field_counts.get(field, 0) + 1
        print("\n  FIELDS CHANGED (how many games each):")
        for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
            print(f"    {field:24} {count}")

        print("\n  SAMPLE CHANGES:")
        for game_id, diffs in list(changed.items())[:6]:
            g = after[game_id]
            print(f"    {g.get('sport')} {g.get('gender')} {g.get('date')}:")
            for field, (old, new) in list(diffs.items())[:4]:
                print(f"      {field}: {describe(old)}  ->  {describe(new)}")


if __name__ == "__main__":
    main()
