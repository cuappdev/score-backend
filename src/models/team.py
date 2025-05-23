from bson.objectid import ObjectId


class Team:
    """
    A model representing a team.

    Attributes:
        - `id`           The ID of the team (auto-generated by MongoDB).
        - `color`        The color of the team.
        - `image`        The image of the team.
        - `b64_image`    The base64 encoded image of the team.
        - `name`         The name of the team.
    """

    def __init__(self, color, name, id=None, image=None, b64_image=None):
        self.id = id if id else str(ObjectId())
        self.color = color
        self.image = image
        self.b64_image = b64_image
        self.name = name

    def to_dict(self):
        """
        Converts the Team object to a dictionary format for MongoDB storage.
        """
        return {
            "_id": self.id,
            "color": self.color,
            "image": self.image,
            "b64_image": self.b64_image,
            "name": self.name,
        }

    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to a Team object.
        """
        return Team(
            id=data.get("_id"),
            color=data.get("color"),
            image=data.get("image"),
            b64_image=data.get("b64_image"),
            name=data.get("name"),
        )
