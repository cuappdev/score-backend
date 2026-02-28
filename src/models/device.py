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
        return {
            "_id": self.id,
            "device_id": self.device_id
        }
    
    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to a Device object.
        """

        return Device(
            id=data.get("_id"),
            device_id=data.get("device_id"),
            current_fcm_token=data.get("current_fcm_token"),
            games=data.get("games"),
            sports=data.get("sports")
        )