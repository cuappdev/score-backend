from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

if os.getenv("STAGE") == "local":
  file_name = "ca-certificate.crt"
  use_tls = os.getenv("MONGO_URI") != "mongodb://localhost:27017/"
else:
  file_name = "/etc/ssl/ca-certificate.crt"
  use_tls = True

if use_tls:
    client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsCAFile=file_name)
else:
    client = MongoClient(os.getenv("MONGO_URI"))

db = client[os.getenv("MONGO_DB", "score_db")]
