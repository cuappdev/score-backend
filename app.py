import logging
import argparse
from flask import Flask
from flask_graphql import GraphQLView
from flask_apscheduler import APScheduler
from graphene import Schema
from src.schema import Query, Mutation
from src.scrapers.games_scraper import fetch_game_schedule
from src.scrapers.youtube_stats import fetch_videos
from src.utils.team_loader import TeamLoader

app = Flask(__name__)

# Set up the scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

schema = Schema(query=Query, mutation=Mutation)

def create_context():
    return {
        "team_loader": TeamLoader()
    }

app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True, get_context=create_context)
)

# Setup command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Skip scraping tasks, for dev purposes.")
    parser.add_argument(
        "--no-scrape",
        action="store_true",
        help="Skips scraping tasks if set, useful for frontend development.",
    )
    return parser.parse_args()

args = parse_args()
if not args.no_scrape:
    @scheduler.task("interval", id="scrape_schedules", seconds=3600)

    def scrape_schedules():
        logging.info("Scraping game schedules...")
        fetch_game_schedule()

    @scheduler.task("interval", id="scrape_schedules", seconds=43200)
    def scrape_videos():
        logging.info("Scraping YouTube videos...")
        fetch_videos()

    scrape_schedules()
    scrape_videos()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)