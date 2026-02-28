from bson.objectid import ObjectId

from src.utils.convert_to_utc import to_datetime


def _normalize_token(value):
    """Return stripped string or empty string; handle None."""
    if value is None:
        return ""
    return str(value).strip()


class Device:
    """
    A model representing a device.

    Attributes:
        - device_id: The id of the device.
        - current_fcm_token: The FCM token of the device.
        - games: The games preferences of the device.
        - sports: The sports preferences of the device.
        - token_update_date: When the FCM token was last updated (datetime or None).
    """

    def __init__(self, device_id, current_fcm_token, games, sports, token_update_date=None, id=None):
        self.id = id if id else str(ObjectId())
        self.device_id = str(device_id).strip() if device_id else ""
        self.current_fcm_token = _normalize_token(current_fcm_token)
        self.games = games if games is not None else []
        self.sports = sports if sports is not None else []
        self.token_update_date = token_update_date  # datetime or None

    def to_dict(self):
        """Payload for $set (excludes _id so we don't try to update it)."""
        payload = {
            "device_id": self.device_id,
            "current_fcm_token": self.current_fcm_token,
            "games": self.games or [],
            "sports": self.sports or [],
        }
        if self.token_update_date is not None:
            payload["token_update_date"] = self.token_update_date
        return payload
    
    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to a Device object.
        Handles token_update_date as datetime or string.
        """
        if not data:
            return None
        doc_id = data.get("_id")
        raw_date = data.get("token_update_date")
        return Device(
            device_id=data.get("device_id"),
            current_fcm_token=data.get("current_fcm_token"),
            games=data.get("games") or [],
            sports=data.get("sports") or [],
            token_update_date=to_datetime(raw_date) if raw_date is not None else raw_date,
            id=str(doc_id) if doc_id else None,
        )