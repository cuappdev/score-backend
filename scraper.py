import logging
import time
from flask import Flask
from flask_apscheduler import APScheduler
import signal
import sys
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos

app = Flask(__name__)

# Set up the scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

@scheduler.task("interval", id="scrape_schedules", seconds=300)
def scrape_schedules():
    start_time = time.time()
    logging.info("Starting scraping games")
    fetch_game_schedule()
    elapsed_time = time.time() - start_time
    logging.info(f"Completed scraping games in {elapsed_time:.2f} seconds")

@scheduler.task("interval", id="scrape_videos", seconds=43200)
def scrape_videos():
    logging.info("Scraping YouTube videos")
    fetch_videos()

def signal_handler(sig, frame):
    scheduler.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    scheduler.start()
    scrape_schedules()
    scrape_videos()
    app.run(host="0.0.0.0", port=8001)
