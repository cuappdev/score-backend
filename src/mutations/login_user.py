from graphql import GraphQLError
from graphene import Mutation, String, Field

from flask_jwt_extended import create_access_token, create_refresh_token
from src.database import db


class LoginUser(Mutation):
    class Arguments:
        net_id = String(required=True, description="User's net ID (e.g. Cornell netid).")

    access_token = String()
    refresh_token = String()

    def mutate(self, info, net_id):
        user = db["users"].find_one({"net_id": net_id})
        if not user:
            raise GraphQLError("User not found.")
        identity = str(user["_id"])
        return LoginUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
