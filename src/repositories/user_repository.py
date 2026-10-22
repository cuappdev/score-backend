from bson import ObjectId

from src.database import db
from src.models.user import User


class UserRepository:
    @staticmethod
    def insert(user):
        result = db["users"].insert_one(user.to_dict())
        user.id = result.inserted_id
        return user

    @staticmethod
    def find_by_firebase_uid(firebase_uid):
        return User.from_dict(db["users"].find_one({"firebase_uid": firebase_uid}))

    @staticmethod
    def find_by_id(user_id):
        return User.from_dict(db["users"].find_one({"_id": ObjectId(user_id)}))

    @staticmethod
    def delete_by_id(user_id):
        """Delete an application user by MongoDB ID."""
        result = db["users"].delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
