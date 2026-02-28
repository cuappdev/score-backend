from bson.objectid import ObjectId

class Device:
    """
    A model representing a device.

    Attributes:
        - `device_id`       The id of the device.
        - `fcm_token`       The FCM token of the device.
        - `games`     The games preferences of the device.
        - `sports`    The sports preferences of the device.
    """

    def __init__(self, device_id, current_fcm_token, games, sports, id=None):
        self.id = id if id else str(ObjectId())
        self.device_id = device_id
        self.current_fcm_token = current_fcm_token
        self.games = games
        self.sports = sports

    def to_dict(self):
        """Payload for $set (excludes _id so we don't try to update it)."""
        return {
            "device_id": self.device_id,
            "current_fcm_token": self.current_fcm_token,
            "games": self.games or [],
            "sports": self.sports or [],
        }
    
    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to a Device object.
        """
        if not data:
            return None
        doc_id = data.get("_id")
        return Device(
            device_id=data.get("device_id"),
            current_fcm_token=data.get("current_fcm_token"),
            games=data.get("games") or [],
            sports=data.get("sports") or [],
            id=str(doc_id) if doc_id else None,
        )