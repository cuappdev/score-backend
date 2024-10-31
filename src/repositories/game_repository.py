from src.database import db
from src.models.game import Game


class GameRepository:
    @staticmethod
    def find_all():
        """
        Retrieve all games from the 'games' collection in MongoDB.

        Returns:
            List[Game]: A list of Game objects.
        """
        game_collection = db["game"]
        games = game_collection.find()
        return [Game.from_dict(game) for game in games]

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
