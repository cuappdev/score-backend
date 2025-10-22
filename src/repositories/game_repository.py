from src.database import db
from src.models.game import Game

import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GameRepository:
    @staticmethod
    def find_all(limit=100, offset=0):
        """
        Retrieve all games from the 'game' collection in MongoDB with pagination.
        """
        request_id = id(threading.current_thread())  # Get a unique ID for this request
        logger.info(
            f"Request {request_id}: Starting find_all with limit={limit}, offset={offset}"
        )

        try:
            game_collection = db["game"]
            logger.info(f"Request {request_id}: Connected to game collection")

            cursor = game_collection.find().skip(offset).limit(limit)
            logger.info(f"Request {request_id}: Created cursor")

            # Force MongoDB to actually perform the query
            games_list = list(cursor)
            logger.info(f"Request {request_id}: Retrieved {len(games_list)} games")

            result = [Game.from_dict(game) for game in games_list]
            logger.info(
                f"Request {request_id}: Converted to {len(result)} Game objects"
            )

            return result
        except Exception as e:
            logger.error(f"Request {request_id}: Error in find_all: {str(e)}")
            raise

    @staticmethod
    def find_by_id(game_id):
        """
        Fetch a game from the MongoDB collection by its ID.

        Args:
            game_id (str): The ID of the game to retrieve.

        Returns:
            Game: The retrieved game or None if not found.
        """
        game_collection = db["game"]
        game_data = game_collection.find_one({"_id": game_id})
        return Game.from_dict(game_data) if game_data else None

    @staticmethod
    def insert(game):
        """
        Inserts a new game into the 'games' collection in MongoDB.
        """
        game_collection = db["game"]
        game_collection.insert_one(game.to_dict())

    @staticmethod
    def delete_by_id(game_id):
        """
        Delete a game from the MongoDB collection by its ID.
        """
        game_collection = db["game"]
        game_collection.delete_one({"_id": game_id})

    @staticmethod
    def update_by_id(game_id, data):
        """
        Update a game in the MongoDB collection by its ID.
        """
        game_collection = db["game"]
        game_collection.update_one({"_id": game_id}, {"$set": data})

    @staticmethod
    def find_by_data(city, date, gender, location, opponent_id, sport, state, time):
        """
        Retrieve a game from the MongoDB collection by its data.
        """
        game_collection = db["game"]
        game_data = game_collection.find_one(
            {
                "city": city,
                "date": date,
                "gender": gender,
                "location": location,
                "opponent_id": opponent_id,
                "sport": sport,
                "state": state,
                "time": time,
            }
        )
        return Game.from_dict(game_data) if game_data else None

    @staticmethod
    def find_by_key_fields(city, date, gender, location, opponent_id, sport, state):
        """
        Find games without time for duplicate games
        """
        game_collection = db["game"]
        games = list(
            game_collection.find(
                {
                    "city": city,
                    "date": date,
                    "gender": gender,
                    "location": location,
                    "opponent_id": opponent_id,
                    "sport": sport,
                    "state": state,
                }
            )
        )

        if not games:
            return None

        if len(games) == 1:
            return Game.from_dict(games[0])

        return [Game.from_dict(game) for game in games]

    @staticmethod
    def find_by_tournament_key_fields(city, date, gender, location, sport, state):
        """
        Find tournament games by location and date (excluding opponent_id).
        This is used when we need to find a tournament game that might have a placeholder team.
        Uses flexible matching to handle TBD/TBA values.
        """
        game_collection = db["game"]
        
        # Build flexible query that can handle TBD/TBA values
        query = {
            "date": date,
            "gender": gender,
            "sport": sport,
        }
        
        # For city, state, and location, use flexible matching
        # This allows finding games even when TBD/TBA values change to real values
        city_conditions = []
        if city:
            city_conditions.append(city)
        else:
            city_conditions = [None]
        
        state_conditions = []
        if state:
            state_conditions.append(state)
        else:
            state_conditions = [None]
        
        location_conditions = []
        if location:
            location_conditions.append(location)
        else:
            location_conditions = [None]
        
        query["city"] = {"$in": city_conditions}
        query["state"] = {"$in": state_conditions}
        query["location"] = {"$in": location_conditions}
        
        games = list(game_collection.find(query))

        if not games:
            return None

        if len(games) == 1:
            return Game.from_dict(games[0])

        return [Game.from_dict(game) for game in games]

    @staticmethod
    def find_by_sport(sport):
        """
        Retrieves all games from the MongoDB collection by its sport.
        """
        game_collection = db["game"]
        games = game_collection.find({"sport": sport})
        return [Game.from_dict(game) for game in games]

    @staticmethod
    def find_by_gender(gender):
        """
        Retrieve all games from the MongoDB collection by its gender.
        """
        game_collection = db["game"]
        games = game_collection.find({"gender": gender})
        return [Game.from_dict(game) for game in games]

    @staticmethod
    def find_by_sport_gender(sport, gender):
        """
        Retrieve all games from the MongoDB collection by its sport and gender.
        """
        game_collection = db["game"]
        games = game_collection.find({"sport": sport, "gender": gender})
        return [Game.from_dict(game) for game in games]

    @staticmethod
    def find_games_by_sport_gender_after_date(sport, gender, after_date=None):
        """
        Find games for a specific sport and gender, optionally after a specific date.
        This method returns raw game data without team information.
        """
        game_collection = db["game"]
        
        query = {
            "sport": sport,
            "gender": gender
        }
        
        if after_date:
            query["utc_date"] = {"$gt": after_date}
        
        games = game_collection.find(query)
        return [Game.from_dict(game) for game in games]
    
    @staticmethod
    def find_by_date(startDate, endDate):
        """
        Retrieve all games from the 'game' collection in MongoDB for games
        between certain dates. 
        """
        game_collection = db["game"]
        
        start_str = startDate.isoformat()
        endDate = endDate.isoformat()
        
        query = {
            "utc_date": {
                "$gte": start_str,
                "$lte": endDate
            }
        }
        
        games = game_collection.find(query)
        return [Game.from_dict(game) for game in games]

    @staticmethod
    def delete_games_by_ids(game_ids):
        """
        Delete games by their IDs.
        """
        game_collection = db["game"]
        result = game_collection.delete_many({"_id": {"$in": game_ids}})
        return result.deleted_count
