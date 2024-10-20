from bson.objectid import ObjectId
from src.database import db


class Game:
    """
    A model representing a game.

    Attributes:
        - `id`: The ID of the game (auto-generated by MongoDB).
        - `city`: The city of the game.
        - `date`: The date of the game.
        - `gender`: The gender of the game.
        = `opponent_id`: The id of the opposing team.
        - `sport`: The sport of the game.
        - `state`: The state of the game.
        = `time`: The time of the game.
    """

    def __init__(self, **kwargs):
        id = kwargs.get("_id")
        self.id = id if id else ObjectId()
        self.city = kwargs.get("city")
        self.date = kwargs.get("date")
        self.gender = kwargs.get("gender")
        self.opponent_id = kwargs.get("opponent_id")
        self.sport = kwargs.get("sport")
        self.state = kwargs.get("state")
        self.time = kwargs.get("time")

    def to_dict(self):
        """
        Converts the Game object to a dictionary format for MongoDB storage.
        """
        return {
            "_id": self.id,
            "city": self.city,
            "date": self.date,
            "gender": self.gender,
            "opponent_id": self.opponent_id,
            "sport": self.sport,
            "state": self.state,
            "time": self.time,
        }

    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to a Game object.
        """
        return Game(
            _id=data.get("_id"),
            city=data.get("city"),
            date=data.get("date"),
            gender=data.get("gender"),
            opponent_id=data.get("opponent_id"),
            sport=data.get("sport"),
            time=data.get("time"),
        )

    @staticmethod
    def get_all_games():
        """
        Retrieve all games from the 'games' collection in MongoDB.
        """
        game_collection = db["game"]
        games = game_collection.find()
        print(games)
        return [Game.from_dict(game) for game in games]

    @staticmethod
    def game(game):
        """
        Inserts a new game into the 'games' collection in MongoDB.
        """
        game_collection = db["game"]
        game_collection.insert_one(game.to_dict())
