from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

file_name = "ca-certificate.crt" if os.getenv("STAGE") == "local" else "/etc/ssl/ca-certificate.crt"

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsCAFile=file_name)
db = client[os.getenv("MONGO_DB", "score-dev")]
