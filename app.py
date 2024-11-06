import logging
from flask import Flask
from flask_graphql import GraphQLView
from flask_apscheduler import APScheduler
from graphene import Schema
from src.schema import Query, Mutation
from src.scrapers.games_scraper import fetch_game_schedule

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


app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True)
)


@scheduler.task("interval", id="scrape_schedules", seconds=3600)
def scrape_schedules():
    logging.info("Scraping game schedules...")

    fetch_game_schedule()


scrape_schedules()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
