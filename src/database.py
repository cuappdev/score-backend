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
    client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsCAFile=file_name)
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
