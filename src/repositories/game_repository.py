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
    def insert(game):
        """
        Inserts a new game into the 'games' collection in MongoDB.
        """
        game_collection = db["game"]
        game_collection.insert_one(game.to_dict())

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
