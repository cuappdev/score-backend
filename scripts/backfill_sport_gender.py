"""
Backfill `sport` and `gender` on stored videos and articles.

Both collections predate those fields. Videos were never given a sport at all
(it was derived at query time), and articles carry `sports_type` but no gender.
This derives both from the title and writes them, so the fields can be queried
and indexed directly.

Safe to re-run: it recomputes from the title every time and only writes rows
whose stored values actually differ. Run it again after changing the extraction
helpers to pick up the new answers.

    python3 scripts/backfill_sport_gender.py              # dry run, writes nothing
    python3 scripts/backfill_sport_gender.py --apply      # write the changes
    python3 scripts/backfill_sport_gender.py --apply --videos-only
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests  # noqa: E402

from src.database import daily_sun_db, db  # noqa: E402
from src.utils.constants import HTTP_REQUEST_HEADERS  # noqa: E402
from src.utils.helpers import (  # noqa: E402
    extract_gender_from_tags,
    extract_gender_from_title,
    extract_sport_from_tags,
    extract_sport_from_title,
)

# extract_sport_type_from_title falls back to this when a headline names no
# sport. It is not a sport, so it should not be treated as one.
UNCLASSIFIED = "sports"


def fetch_article_tags():
    """
    Tags by article slug, from the Daily Sun feed.

    Tags are not stored on our documents, only in the feed, so they have to be
    re-fetched to backfill. Returns an empty mapping if the feed is unreachable;
    the backfill then falls back to titles alone.
    """
    url = os.getenv("DAILY_SUN_URL")
    if not url:
        print("  (DAILY_SUN_URL not set - falling back to headlines only)")
        return {}

    try:
        response = requests.get(url, headers=HTTP_REQUEST_HEADERS, timeout=30)
        response.raise_for_status()
        articles = response.json().get("articles", [])
    except Exception as error:
        print(f"  (could not fetch the Daily Sun feed: {error} - headlines only)")
        return {}

    print(f"  fetched tags for {len(articles)} article(s) from the feed")
    return {a.get("slug"): a.get("tags") for a in articles if a.get("slug")}


def derive(title, stored_sport=None, tags=None):
    """
    Work out (sport, gender) for one row.

    Sport prefers a stored value, then the article's tags, then the headline.
    Tags catch articles whose headline never names the sport. The "sports"
    placeholder is not a stored sport, it only means "unclassified".

    Gender prefers the title, because the single-gender fallback resolves cases
    the tags leave blank (football is tagged without a gender), then the tags.
    """
    sport = stored_sport if stored_sport and stored_sport != UNCLASSIFIED else None
    if not sport:
        sport = extract_sport_from_tags(tags) or extract_sport_from_title(title)

    gender = extract_gender_from_title(title, sport) or extract_gender_from_tags(tags)
    return sport, gender


def plan_updates(docs, title_key="title", sport_key="sport", tags_by_slug=None):
    """
    Return (updates, unresolved) without touching the database.

    updates is a list of (doc, changed_fields). unresolved lists rows where no
    sport could be determined, which are reported rather than written.
    """
    updates, unresolved = [], []

    for doc in docs:
        title = doc.get(title_key) or ""
        tags = (tags_by_slug or {}).get(doc.get("slug"))
        sport, gender = derive(title, doc.get(sport_key), tags)

        if not sport:
            unresolved.append(doc)
            continue

        changed = {}
        if doc.get(sport_key) != sport:
            changed[sport_key] = sport
        if doc.get("gender") != gender:
            changed["gender"] = gender

        if changed:
            updates.append((doc, changed))

    return updates, unresolved


def report(label, total, updates, unresolved, title_key="title"):
    print(f"\n=== {label}: {total} document(s) ===")
    print(f"  to update:   {len(updates)}")
    print(f"  already set: {total - len(updates) - len(unresolved)}")
    print(f"  no sport:    {len(unresolved)}")

    for doc, changed in updates[:10]:
        title = (doc.get(title_key) or "")[:52]
        print(f"    {changed}  <- {title}")
    if len(updates) > 10:
        print(f"    ... and {len(updates) - 10} more")

    for doc in unresolved[:5]:
        print(f"    SKIP (no sport in title): {(doc.get(title_key) or '')[:60]}")
    if len(unresolved) > 5:
        print(f"    ... and {len(unresolved) - 5} more")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    parser.add_argument("--videos-only", action="store_true")
    parser.add_argument("--articles-only", action="store_true")
    args = parser.parse_args()

    do_videos = not args.articles_only
    do_articles = not args.videos_only
    written = 0

    if do_videos:
        collection = db["youtubevideo"]
        docs = list(collection.find())
        # Videos never had a sport field, so there is no stored value to trust.
        updates, unresolved = plan_updates(docs, sport_key="sport")
        report("videos (db.youtubevideo)", len(docs), updates, unresolved)
        if args.apply:
            for doc, changed in updates:
                collection.update_one({"_id": doc["_id"]}, {"$set": changed})
            written += len(updates)

    if do_articles:
        collection = daily_sun_db["news_articles"]
        docs = list(collection.find())
        tags_by_slug = fetch_article_tags()
        # Articles store their sport as sports_type.
        updates, unresolved = plan_updates(
            docs, sport_key="sports_type", tags_by_slug=tags_by_slug
        )
        report("articles (daily_sun_db.news_articles)", len(docs), updates, unresolved)
        if args.apply:
            for doc, changed in updates:
                collection.update_one({"_id": doc["_id"]}, {"$set": changed})
            written += len(updates)

    print()
    if args.apply:
        print(f"Applied: {written} document(s) updated.")
    else:
        print("Dry run, nothing written. Re-run with --apply to write these changes.")


if __name__ == "__main__":
    main()
