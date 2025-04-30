from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pymongo

load_dotenv()

# Determine certificate path and TLS usage
if os.getenv("STAGE") == "local":
    file_name = "ca-certificate.crt"
    use_tls = os.getenv("MONGO_URI") != "mongodb://localhost:27017/"
else:
    file_name = "/etc/ssl/ca-certificate.crt"
    use_tls = True

# Connection pooling settings
max_pool_size = 10  # Maximum number of connections in the pool
min_pool_size = 3  # Minimum number of connections to maintain
max_idle_time_ms = 60000  # 1 minute

# Initialize MongoDB client with optimized settings
if use_tls:
    client = MongoClient(
        os.getenv("MONGO_URI"),
        tls=True,
        tlsCAFile=file_name,
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=max_idle_time_ms,
        waitQueueTimeoutMS=2000,  # Wait 2 seconds for connection before timeout
        retryWrites=True,
        # Remove serverSelectionTimeoutMS to use MongoDB default
    )
else:
    client = MongoClient(
        os.getenv("MONGO_URI"),
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=max_idle_time_ms,
        waitQueueTimeoutMS=2000,
        retryWrites=True,
    )

# Force connection on startup
try:
    client.admin.command("ping")
    print("✅ MongoDB connection successful on startup")
except Exception as e:
    print(f"❌ MongoDB connection failed on startup: {e}")
    raise e

# Access the database
db = client[os.getenv("MONGO_DB", "score_db")]


# Setup indexes only if they don't exist
def setup_database_indexes():
    """Set up MongoDB indexes for optimal query performance"""
    try:
        game_collection = db["game"]

        # Get existing indexes
        existing_indexes = game_collection.index_information()

        # Define indexes we want
        indexes = [
            ("sport", pymongo.ASCENDING),
            ("date", pymongo.ASCENDING),
            ("gender", pymongo.ASCENDING),
            [("sport", pymongo.ASCENDING), ("gender", pymongo.ASCENDING)],
            ("date", pymongo.DESCENDING),
        ]

        # Create only missing indexes
        for index in indexes:
            # Convert single field index to list format for consistency
            index_list = [index] if not isinstance(index, list) else index

            # Generate index name
            index_name = "_".join(
                [f"{field}_{direction}" for field, direction in index_list]
            )

            if index_name not in existing_indexes:
                game_collection.create_index(index_list, background=True)
                print(f"Created index: {index_name}")

        print("✅ MongoDB indexes verified")
    except Exception as e:
        print(f"❌ Failed to verify MongoDB indexes: {e}")
        # Don't raise exception here, just log the error


# Setup indexes
setup_database_indexes()
