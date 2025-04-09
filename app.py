import logging
import argparse
from flask import Flask
from flask_graphql import GraphQLView
from graphene import Schema
from src.schema import Query, Mutation
from src.utils.team_loader import TeamLoader
import os
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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

def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
