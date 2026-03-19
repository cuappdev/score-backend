from graphql import GraphQLError
from graphene import Mutation, String

from flask_jwt_extended import create_access_token, create_refresh_token
from src.database import db


class SignupUser(Mutation):
    class Arguments:
        net_id = String(required=True, description="User's net ID (e.g. Cornell netid).")
        name = String(required=False, description="Display name.")
        email = String(required=False, description="Email address.")

    access_token = String()
    refresh_token = String()

    def mutate(self, info, net_id, name=None, email=None):
        if db["users"].find_one({"net_id": net_id}):
            raise GraphQLError("Net ID already exists.")
        user_doc = {
            "net_id": net_id,
            "favorite_game_ids": [],
        }
        if name is not None:
            user_doc["name"] = name
        if email is not None:
            user_doc["email"] = email
        result = db["users"].insert_one(user_doc)
        identity = str(result.inserted_id)
        return SignupUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
