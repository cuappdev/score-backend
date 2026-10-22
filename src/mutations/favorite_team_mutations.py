from graphql import GraphQLError
from graphene import Boolean, Mutation, String

from flask_jwt_extended import get_jwt_identity
from src.services.user_service import UserService
from src.utils.graphql_errors import graphql_jwt_required


class AddFavoriteTeam(Mutation):
    class Arguments:
        gender = String(
            required=True,
            description="Gender of the team, such as Mens or Womens.",
        )
        sport = String(
            required=True,
            description="Sport of the team"
        )
    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, gender, sport):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        if not gender.strip() or not sport.strip():
            raise GraphQLError("Gender and sport are required.")
        if not UserService.add_favorite_team(user_id, gender, sport):
            raise GraphQLError("Could not add team to favorites.")
        return AddFavoriteTeam(success=True)


class RemoveFavoriteTeam(Mutation):
    class Arguments:
        gender = String(
            required=True,
            description="Gender of the team, such as Mens or Womens.",
        )
        sport = String(
            required=True,
            description="Sport of the team",
        )

    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, gender, sport):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        if not gender.strip() or not sport.strip():
            raise GraphQLError("Gender and sport are required.")
        if not UserService.remove_favorite_team(user_id, gender, sport):
            raise GraphQLError("Could not remove team from favorites.")
        return RemoveFavoriteTeam(success=True)
