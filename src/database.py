from pymongo import MongoClient
import os
from dotenv import load_dotenv
import threading
import time

load_dotenv()

# Determine certificate path and TLS usage
if os.getenv("STAGE") == "local":
    file_name = "ca-certificate.crt"
    use_tls = os.getenv("MONGO_URI") != "mongodb://localhost:27017/"
else:
    file_name = "/etc/ssl/ca-certificate.crt"
    use_tls = True

# Initialize MongoDB client
if use_tls:
    client = MongoClient(
        os.getenv("MONGO_URI"),
        tls=True,
        tlsCAFile=file_name,
    )
else:
    client = MongoClient(os.getenv("MONGO_URI"))

# Force connection on startup
try:
    client.admin.command("ping")
    print("✅ MongoDB connection successful on startup")
except Exception as e:
    print(f"❌ MongoDB connection failed on startup: {e}")
    raise e


# Start a keep-alive thread
def keep_connection_alive():
    while True:
        try:
            client.admin.command("ping")
            print("🔁 MongoDB keep-alive ping successful")
        except Exception as e:
            print(f"⚠️ MongoDB keep-alive ping failed: {e}")
        time.sleep(300)  # ping every 5 minutes


threading.Thread(target=keep_connection_alive, daemon=True).start()

# Access the database
db = client[os.getenv("MONGO_DB", "score_db")]
print("Total games in DB:", db["game"].count_documents({}))

def setup_database_indexes():
    """Set up MongoDB indexes for optimal query performance"""
    try:
        game_collection = db["game"]

        # Create single field indexes for commonly queried fields
        game_collection.create_index([("sport", 1)], background=True)
        game_collection.create_index([("date", 1)], background=True)
        game_collection.create_index([("gender", 1)], background=True)

        # Create compound indexes for common query combinations
        game_collection.create_index([("sport", 1), ("gender", 1)], background=True)

        # Index for sorting operations
        game_collection.create_index([("date", -1)], background=True)
        
        # Index to have unique games so we won't add duplicates
        game_collection.create_index(
            [
                ("sport", 1),
                ("gender", 1),
                ("date", 1),
                ("opponent_id", 1),
                ("city", 1),
                ("state", 1),
                ("location", 1),
            ],
            unique=True,
            background=True
        )

        print("✅ MongoDB indexes created successfully")
    except Exception as e:
        print(f"❌ Failed to create MongoDB indexes: {e}")
        raise e


setup_database_indexes()
