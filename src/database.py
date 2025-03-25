from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

if os.getenv("STAGE") == "local":
  file_name = "ca-certificate.crt"
  use_tls = "localhost" not in os.getenv("MONGO_URI")
else:
  file_name = "/etc/ssl/ca-certificate.crt"
  use_tls = True

if use_tls:
    client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsCAFile=file_name)
else:
    client = MongoClient(os.getenv("MONGO_URI"))

db = client[os.getenv("MONGO_DB", "score_db")]
daily_sun_db = client[os.getenv("DAILY_SUN_DB", "daily_sun_db")]
