from bson import ObjectId
from graphql import GraphQLError
from graphene import Mutation, String, Boolean

from flask_jwt_extended import get_jwt_identity, jwt_required
from src.database import db
from src.services.game_service import GameService


class AddFavoriteGame(Mutation):
    class Arguments:
        game_id = String(required=True, description="ID of the game to add to favorites.")

    success = Boolean()

    @jwt_required()
    def mutate(self, info, game_id):
        if not GameService.get_game_by_id(game_id):
            raise GraphQLError("Game not found.")
        user_id = get_jwt_identity()
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"favorite_game_ids": game_id}},
        )
        return AddFavoriteGame(success=True)
