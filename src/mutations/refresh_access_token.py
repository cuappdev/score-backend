from graphene import Mutation, String
from graphql import GraphQLError

from flask_jwt_extended import create_access_token, get_jwt_identity

from src.services.user_service import UserService
from src.utils.graphql_errors import graphql_jwt_required


class RefreshAccessToken(Mutation):
    new_access_token = String()

    @graphql_jwt_required(refresh=True)
    def mutate(self, info):
        identity = get_jwt_identity()
        if not UserService.require_user(identity):
            raise GraphQLError("User not found.")
        return RefreshAccessToken(
            new_access_token=create_access_token(identity=identity),
        )
