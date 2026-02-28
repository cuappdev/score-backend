from src.database import db
from src.models.device import Device
from src.utils.convert_to_utc import to_datetime
from datetime import datetime, timezone

class DeviceRepository:
    @staticmethod
    def upsert(device_id, current_fcm_token, games, sports):
        """
        Upsert a device into the 'devices' collection in MongoDB.
        If the device exists and the FCM token is different, token_update_date is set to now.
        Returns the Device after upsert.
        """
        device_collection = db["devices"]
        existing = device_collection.find_one({"device_id": (device_id or "").strip()})

        token_changed = True
        if existing:
            existing_token = (existing.get("current_fcm_token") or "").strip()
            incoming_token = (current_fcm_token or "").strip()
            token_changed = existing_token != incoming_token

        if token_changed or not existing:
            token_update_date = datetime.now(timezone.utc)
        else:
            raw = existing.get("token_update_date")
            token_update_date = to_datetime(raw) if raw is not None else datetime.now(timezone.utc)

        device = Device(
            device_id=device_id,
            current_fcm_token=current_fcm_token,
            games=games,
            sports=sports,
            token_update_date=token_update_date,
        )
        device_collection.update_one(
            {"device_id": device.device_id},
            {"$set": device.to_dict()},
            upsert=True
        )
        doc = device_collection.find_one({"device_id": device.device_id})
        return Device.from_dict(doc)