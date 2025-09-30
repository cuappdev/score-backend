import logging
import argparse
from flask import Flask, request, g
import time
from flask_graphql import GraphQLView
from graphene import Schema
from src.schema import Query, Mutation
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos
from src.scrapers.daily_sun_scrape import fetch_news
from src.services.article_service import ArticleService
from src.utils.team_loader import TeamLoader
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.before_request
def start_timer():
    g.start = time.time()

    if request.path == "/graphql" and request.method == "POST":
        try:
            # Try to extract the GraphQL query name for better logging
            query_data = request.get_json()
            if query_data and "query" in query_data:
                g.query = query_data["query"].split("{", 1)[0].strip()
                logging.info(
                    f"[{time.strftime('%H:%M:%S')}] --> GraphQL {g.query} started"
                )
        except:
            pass

    logging.info(
        f"[{time.strftime('%H:%M:%S')}] --> {request.method} {request.path} started"
    )


@app.after_request
def log_response_time(response):
    if hasattr(g, "start"):
        duration = time.time() - g.start

        if duration > 5.0:  # Flag slow requests
            if hasattr(g, "query"):
                logging.warning(
                    f"[{time.strftime('%H:%M:%S')}] <-- SLOW GraphQL {g.query} ({duration:.2f}s)"
                )
            else:
                logging.warning(
                    f"[{time.strftime('%H:%M:%S')}] <-- SLOW {request.method} {request.path} ({duration:.2f}s)"
                )
        else:
            if hasattr(g, "query"):
                logging.info(
                    f"[{time.strftime('%H:%M:%S')}] <-- GraphQL {g.query} finished in {duration:.2f}s"
                )
            else:
                logging.info(
                    f"[{time.strftime('%H:%M:%S')}] <-- {request.method} {request.path} finished in {duration:.2f}s"
                )
    return response


# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

schema = Schema(query=Query, mutation=Mutation)


def create_context():
    return {"team_loader": TeamLoader()}


app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view(
        "graphql", schema=schema, graphiql=True, get_context=create_context
    ),
)

# Setup command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Skip scraping tasks, for dev purposes.")
    parser.add_argument(
        "--no-scrape",
        action="store_true",
        help="Skips scraping tasks if set, useful for frontend development.",
    )
    parser.add_argument(
        "--no-daily-sun",
        action="store_true",
        help="Skips using the Daily Sun page for alerts",
    )
    return parser.parse_args()

# Only parse arguments when running directly (not when imported by gunicorn)
if __name__ == "__main__":
    args = parse_args()
else:
    # Default args when imported by gunicorn
    class DefaultArgs:
        no_scrape = False
        no_daily_sun = False
    args = DefaultArgs()

def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Only run scraping tasks if not disabled
if not args.no_scrape:
    from flask_apscheduler import APScheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task("interval", id="scrape_schedules", seconds=43200) # 12 hours
    def scrape_schedules():
        logging.info("Scraping game schedules...")
        fetch_game_schedule()

    @scheduler.task("interval", id="scrape_videos", seconds=43200) # 12 hours
    def scrape_videos():
        logging.info("Scraping YouTube videos...")
        fetch_videos()

    scrape_schedules()
    scrape_videos()

if not args.no_daily_sun and not args.no_scrape:
    @scheduler.task("interval", id="scrape_daily_sun", seconds=3600)
    def scrape_daily_sun():
        logging.info("Getting Daily Sun Sports News...")
        fetch_news()

    @scheduler.task("interval", id="cleanse_daily_sun_db", seconds=604800) # 1 week
    def cleanse_daily_sun_db():
        logging.info("Cleaning the Daily Sun database from old articles...")
        ArticleService.cleanse_old_articles()

    scrape_daily_sun()
    cleanse_daily_sun_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
