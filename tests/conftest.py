"""
Shared test setup.

src.utils.constants reads JWT_SECRET_KEY from the environment at import time, so
it has to exist before anything under src is imported. Tests never use the value.
"""
import os

os.environ.setdefault("JWT_SECRET_KEY", "test-only-not-a-real-secret")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/")
os.environ.setdefault("MONGO_DB", "test_db")
