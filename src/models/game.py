from bson.objectid import ObjectId
from src.database import db


class Game:
    """
    A model representing a game.

    Attributes:
        - `city`        The city of the game.
        - `date`        The date of the game.
        - `gender`      The gender of the game.
        - `location`    The location of the game. (optional)
        - `opponent_id` The id of the opposing team.
        - `result`      The result of the game. (optional)
        - `sport`       The sport of the game.
        - `state`       The state of the game.
        - `time`        The time of the game. (optional)
    """

    def __init__(
        self,
        city,
        date,
        gender,
        opponent_id,
        sport,
        state,
        id=None,
        location=None,
        result=None,
        time=None,
    ):
        self.id = id if id else str(ObjectId())
        self.city = city
        self.date = date
        self.gender = gender
        self.location = location
        self.opponent_id = opponent_id
        self.result = result
        self.sport = sport
        self.state = state
        self.time = time

    def to_dict(self):
        """
        Converts the Game object to a dictionary format for MongoDB storage.
        """
        return {
            "_id": self.id,
            "city": self.city,
            "date": self.date,
            "gender": self.gender,
            "location": self.location,
            "opponent_id": self.opponent_id,
            "result": self.result,
            "sport": self.sport,
            "state": self.state,
            "time": self.time,
        }

    @staticmethod
    def from_dict(data) -> None:
        """
        Converts a MongoDB document to a Game object.
        """
        return Game(
            id=data.get("_id"),
            city=data.get("city"),
            date=data.get("date"),
            gender=data.get("gender"),
            location=data.get("location"),
            opponent_id=data.get("opponent_id"),
            result=data.get("result"),
            sport=data.get("sport"),
            state=data.get("state"),
            time=data.get("time"),
        )
