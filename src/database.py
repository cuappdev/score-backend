from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["score_db"]


def init_db():
    print("Database initialized")
