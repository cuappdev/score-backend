import logging
import os
import signal
import sys
import time
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_graphql import GraphQLView
from graphene import Schema
from src.schema import Query, Mutation
from src.utils.constants import JWT_SECRET_KEY
from src.utils.team_loader import TeamLoader
from src.database import db, client

# NOTE: Background scraping and all APScheduler jobs intentionally live in
# `scraper.py` (the dedicated `thestack_scraper` service), NOT here. When
# Gunicorn imports this module it must only initialize Flask/GraphQL so that
# web workers boot in milliseconds and never block on external websites,
# YouTube, or MongoDB DDL.

import firebase_admin
from firebase_admin import credentials

SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


def initialize_firebase():
    """Initialize Firebase Admin once so Firebase ID tokens can be verified."""
    if not firebase_admin._apps:
        if not SERVICE_ACCOUNT_PATH:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS is not set. "
                "Set it to the Firebase service-account JSON path."
            )
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        logging.info("Firebase app initialized.")
    return firebase_admin.get_app()


initialize_firebase()

app = Flask(__name__)

# CORS: allow frontend (different origin) to call this API
CORS(app, supports_credentials=True)

# JWT config
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    """Reject the request if the token's jti is in the blocklist (e.g. after logout)."""
    jti = jwt_payload["jti"]
    return db["token_blocklist"].find_one({"jti": jti}) is not None


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

schema = Schema(query=Query, mutation=Mutation, auto_camelcase=True)


def create_context():
    return {"team_loader": TeamLoader()}


@app.route("/health")
def health_check():
    try:
        client.admin.command("ping")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception:
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 503


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
    # Local development only. In production the app is served by Gunicorn
    # (see Dockerfile) and background jobs are run by scraper.py.
    app.run(debug=True, host="0.0.0.0", port=8000)
