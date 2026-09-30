"""Scrape Cornell men's soccer into JSON without connecting to the database.

Run from the repository root:
    python -m src.scrapers.roster_scraper --output /tmp/soccer-roster.json
"""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROSTER_URL = "https://cornellbigred.com/sports/mens-soccer/roster"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}


def parse_roster(html, source_url=ROSTER_URL):
    """Extract one entry per player, including lazy-loaded headshot URLs."""
    soup = BeautifulSoup(html, "html.parser")
    heading = next(
        (h for h in soup.select("h1, h2") if "Soccer Roster" in h.get_text()), None
    )
    title = heading.get_text(" ", strip=True) if heading else ""
    season_match = re.search(r"\b(\d{4}(?:-\d{2,4})?)\b", title)
    players = []
    seen_ids = set()

    for row in soup.select("li.sidearm-roster-player"):
        def text(selector):
            element = row.select_one(selector)
            return (element.get_text(" ", strip=True) or None) if element else None

        player_id = row.get("data-player-id")
        name = text(".sidearm-roster-player-name a")
        if not player_id or not name:
            raise ValueError("Roster entry is missing its player ID or name.")
        if player_id in seen_ids:
            continue
        seen_ids.add(player_id)

        image = row.select_one(".sidearm-roster-player-image img")
        image_path = (image.get("data-src") or image.get("src")) if image else None
        profile_path = row.get("data-player-url")
        players.append({
            "source_player_id": player_id,
            "name": name,
            "jersey_number": text(".sidearm-roster-player-jersey-number"),
            "position": text(".sidearm-roster-player-position-long-short"),
            "class_year": text(".sidearm-roster-player-academic-year:not(.hide-on-large)")
            or text(".sidearm-roster-player-academic-year"),
            "height": text(".sidearm-roster-player-height"),
            "hometown": text(".sidearm-roster-player-hometown"),
            "image_url": urljoin(source_url, image_path) if image_path else None,
            "profile_url": urljoin(source_url, profile_path) if profile_path else None,
        })

    if not players:
        raise ValueError("No players found; the roster page may have changed.")

    return {
        "sport": "Soccer",
        "gender": "Mens",
        "season": season_match.group(1) if season_match else None,
        "source_url": source_url,
        "players": players,
    }


def fetch_roster():
    """Fetch the current men's soccer roster with a bounded request timeout."""
    response = requests.get(ROSTER_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return parse_roster(response.content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Save JSON here; otherwise print it.")
    parser.add_argument("--html", type=Path, help="Parse saved HTML instead of fetching.")
    args = parser.parse_args()
    roster = parse_roster(args.html.read_bytes()) if args.html else fetch_roster()
    output = json.dumps(roster, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Saved {len(roster['players'])} players to {args.output}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
