from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["score_db"]


def init_db():
    """
    Initializes the database connection.

    This function should be called once at the start of the application and will create the
    database and collections if they don't exist.
    """
    print(db.list_collection_names())
    print("Database initialized")
