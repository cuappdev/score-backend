import logging
import argparse
from flask import Flask, request, g
import time
from flask_graphql import GraphQLView
from graphene import Schema
from src.schema import Query, Mutation
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


def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
