from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsCAFile="/etc/ssl/ca-certificate.crt")
db = client[os.getenv("MONGO_DB")]
