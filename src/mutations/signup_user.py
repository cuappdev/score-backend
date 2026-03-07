from graphql import GraphQLError
from graphene import Mutation, String

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import create_access_token, create_refresh_token
from src.database import db


class SignupUser(Mutation):
    class Arguments:
        id_token = String(required=True, description="Firebase ID token from the client.")
        name = String(required=False, description="Display name.")
        email = String(required=False, description="Email (overrides token email if provided).")

    access_token = String()
    refresh_token = String()

    def mutate(self, info, id_token, name=None, email=None):
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except Exception:
            raise GraphQLError("Invalid or expired token.")

        firebase_uid = decoded["uid"]
        if db["users"].find_one({"firebase_uid": firebase_uid}):
            raise GraphQLError("User already exists.")

        email = email or decoded.get("email")
        user_doc = {
            "firebase_uid": firebase_uid,
            "email": email,
            "favorite_game_ids": [],
        }
        if name is not None:
            user_doc["name"] = name
        result = db["users"].insert_one(user_doc)
        identity = str(result.inserted_id)
        return SignupUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
