import logging
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from src.database import db
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos
from src.scrapers.daily_sun_scrape import fetch_news
from src.services.article_service import ArticleService

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Hard wall-clock ceiling for a single game-schedule run. fetch_game_schedule()
# bounds itself too, but this watchdog guarantees the APScheduler job slot is
# always released even if a worker thread wedges, which is what caused
# "maximum number of running instances reached (1)" for hours (report F3).
GAME_SCRAPE_DEADLINE_SECONDS = 15 * 60


def _run_supervised(name, func, deadline_seconds):
    """Run ``func`` with a wall-clock deadline and consistent start/finish logs.

    The function is executed in a short-lived worker thread. If it does not
    finish within ``deadline_seconds`` we log loudly and return so the caller
    (an APScheduler job) can finish and free its ``max_instances`` slot. The
    orphaned thread cannot block future runs; because every network call now
    has its own timeout, it will also unwind on its own.
    """
    start = time.time()
    logger.info("Starting job %s", name)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=name)
    future = executor.submit(func)
    try:
        future.result(timeout=deadline_seconds)
        logger.info("Completed job %s in %.2f seconds", name, time.time() - start)
    except FutureTimeoutError:
        logger.error(
            "Job %s exceeded %ss deadline; abandoning this run and freeing the "
            "scheduler slot (a later trigger will retry)",
            name,
            deadline_seconds,
        )
    except Exception:
        logger.exception("Job %s failed after %.2f seconds", name, time.time() - start)
    finally:
        # Do not block on a wedged thread; cancel_futures is a no-op for the
        # already-running task but prevents the executor from waiting on it.
        executor.shutdown(wait=False, cancel_futures=True)


def scrape_schedules():
    _run_supervised("scrape_schedules", fetch_game_schedule, GAME_SCRAPE_DEADLINE_SECONDS)


def scrape_videos():
    _run_supervised("scrape_videos", fetch_videos, 10 * 60)


def scrape_daily_sun():
    _run_supervised("scrape_daily_sun", fetch_news, 10 * 60)


def cleanse_daily_sun_db():
    _run_supervised(
        "cleanse_daily_sun_db", ArticleService.cleanse_old_articles, 5 * 60
    )


def cleanse_token_blocklist():
    """Remove expired JWTs so the blocklist collection doesn't grow forever."""
    result = db["token_blocklist"].delete_many(
        {"expires_at": {"$lt": datetime.now(timezone.utc)}}
    )
    if result.deleted_count:
        logger.info(
            "Cleansed %s expired token(s) from blocklist", result.deleted_count
        )


scheduler = BackgroundScheduler(
    daemon=True,
    # One owner per job across the whole deployment. coalesce collapses any
    # missed runs into a single run, and a stuck job can never stack up.
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": 300,
    },
)


def signal_handler(sig, frame):
    logging.info("Shutting down scheduler...")
    scheduler.shutdown(wait=False)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # This process (thestack_scraper) is the single scheduler owner for every
    # background job. The web process (app.py) runs none of these.
    scheduler.add_job(
        scrape_schedules, "interval", seconds=60 * 60, id="scrape_schedules"
    )
    scheduler.add_job(
        scrape_videos, "interval", seconds=60 * 60 * 12, id="scrape_videos"
    )
    scheduler.add_job(
        scrape_daily_sun, "interval", seconds=60 * 60, id="scrape_daily_sun"
    )
    scheduler.add_job(
        cleanse_daily_sun_db,
        "interval",
        seconds=60 * 60 * 24 * 7,
        id="cleanse_daily_sun_db",
    )
    scheduler.add_job(
        cleanse_token_blocklist,
        "interval",
        seconds=60 * 60 * 24,
        id="cleanse_token_blocklist",
    )
    scheduler.start()

    # Prime data once on boot so a fresh deploy isn't empty until the first
    # interval fires.
    scrape_schedules()
    scrape_videos()
    scrape_daily_sun()

    signal.pause()
