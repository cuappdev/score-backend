from graphql import GraphQLError
from graphene import Mutation, String

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import create_access_token, create_refresh_token
from pymongo.errors import DuplicateKeyError
from src.database import db

_TOKEN_ERRORS = (
    firebase_auth.InvalidIdTokenError,
    firebase_auth.ExpiredIdTokenError,
    firebase_auth.RevokedIdTokenError,
)


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
        except _TOKEN_ERRORS as err:
            raise GraphQLError("Invalid or expired token.") from err
        except ValueError as err:
            raise GraphQLError("Invalid or expired token.") from err

        firebase_uid = decoded.get("uid")
        if firebase_uid is None:
            raise GraphQLError("Token missing uid") from KeyError("uid")

        email = email or decoded.get("email")
        user_doc = {
            "firebase_uid": firebase_uid,
            "email": email,
            "favorite_game_ids": [],
        }
        if name is not None:
            user_doc["name"] = name
        try:
            result = db["users"].insert_one(user_doc)
        except DuplicateKeyError as err:
            raise GraphQLError("User already exists.") from err
        identity = str(result.inserted_id)
        return SignupUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
