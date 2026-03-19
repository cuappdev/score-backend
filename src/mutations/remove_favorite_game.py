from bson import ObjectId
from graphene import Mutation, String, Boolean

from flask_jwt_extended import get_jwt_identity, jwt_required
from src.database import db


class RemoveFavoriteGame(Mutation):
    class Arguments:
        game_id = String(required=True, description="ID of the game to remove from favorites.")

    success = Boolean()

    @jwt_required()
    def mutate(self, info, game_id):
        user_id = get_jwt_identity()
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"favorite_game_ids": game_id}},
        )
        return RemoveFavoriteGame(success=True)
