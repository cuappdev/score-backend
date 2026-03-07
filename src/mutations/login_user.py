from graphql import GraphQLError
from graphene import Mutation, String

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import create_access_token, create_refresh_token
from src.database import db


class LoginUser(Mutation):
    class Arguments:
        id_token = String(required=True, description="Firebase ID token from the client.")

    access_token = String()
    refresh_token = String()

    def mutate(self, info, id_token):
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception:
            raise GraphQLError("Invalid or expired token.")

        firebase_uid = decoded["uid"]
        user = db["users"].find_one({"firebase_uid": firebase_uid})
        if not user:
            raise GraphQLError("User not found.")
        identity = str(user["_id"])
        return LoginUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
