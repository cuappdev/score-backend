from graphql import GraphQLError
from graphene import Boolean, Mutation, String

from flask_jwt_extended import get_jwt_identity
from src.services.game_service import GameService
from src.services.user_service import UserService
from src.utils.graphql_errors import graphql_jwt_required


class AddFavoriteGame(Mutation):
    class Arguments:
        game_id = String(required=True, description="ID of the game to add to favorites.")

    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, game_id):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        if not GameService.get_game_by_id(game_id):
            raise GraphQLError("Game not found.")
        if not UserService.add_favorite_game(user_id, game_id):
            raise GraphQLError("Could not add game to favorites.")
        return AddFavoriteGame(success=True)


class RemoveFavoriteGame(Mutation):
    class Arguments:
        game_id = String(required=True, description="ID of the game to remove from favorites.")

    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, game_id):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        UserService.remove_favorite_game(user_id, game_id)
        return RemoveFavoriteGame(success=True)
