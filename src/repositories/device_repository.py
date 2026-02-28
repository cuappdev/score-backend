from src.database import db
from src.models.device import Device
from bson.objectid import ObjectId

class DeviceRepository:
    @staticmethod
    def upsert(device_id, current_fcm_token, games, sports):
        """
        Upsert a device into the 'devices' collection in MongoDB.
        Returns the Device after upsert.
        """
        device = Device(device_id, current_fcm_token, games, sports)
        device_collection = db["devices"]
        device_collection.update_one(
            {"device_id": device.device_id},
            {"$set": device.to_dict()},
            upsert=True
        )
        doc = device_collection.find_one({"device_id": device.device_id})
        return Device.from_dict(doc)