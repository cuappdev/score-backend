import logging
import time
import signal
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

scheduler = BackgroundScheduler(daemon=True)


def scrape_schedules():
    start_time = time.time()
    logging.info("Starting scraping games")
    fetch_game_schedule()
    elapsed_time = time.time() - start_time
    logging.info(f"Completed scraping games in {elapsed_time:.2f} seconds")


def scrape_videos():
    logging.info("Scraping YouTube videos")
    fetch_videos()


def signal_handler(sig, frame):
    logging.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    scheduler.add_job(scrape_schedules, "interval", seconds=300, id="scrape_schedules")
    scheduler.add_job(scrape_videos, "interval", seconds=43200, id="scrape_videos")
    scheduler.start()
    scrape_schedules()
    scrape_videos()

    signal.pause()
