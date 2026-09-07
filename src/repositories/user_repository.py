from bson import ObjectId
from pymongo import ReturnDocument

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
    def add_favorite_game(user_id, game_id):
        document = db["users"].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"favorite_game_ids": str(game_id)}},
            return_document=ReturnDocument.AFTER,
        )
        return User.from_dict(document)

    @staticmethod
    def remove_favorite_game(user_id, game_id):
        document = db["users"].find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$pull": {"favorite_game_ids": str(game_id)}},
            return_document=ReturnDocument.AFTER,
        )
        return User.from_dict(document)
