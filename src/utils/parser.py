import argparse
import logging
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-games", action="store_true")
    args = parser.parse_args()
    if not args.no_games:
        fetch_game_schedule()
        fetch_videos()
    else:
        logging.info("skipping game schedule scraping")
