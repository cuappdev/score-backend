from graphql import GraphQLError
from graphene import Mutation, String

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import create_access_token, create_refresh_token
from src.database import db

_TOKEN_ERRORS = (
    firebase_auth.InvalidIdTokenError,
    firebase_auth.ExpiredIdTokenError,
    firebase_auth.RevokedIdTokenError,
)


class LoginUser(Mutation):
    class Arguments:
        id_token = String(required=True, description="Firebase ID token from the client.")

    access_token = String()
    refresh_token = String()

    def mutate(self, info, id_token):
        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except _TOKEN_ERRORS as err:
            raise GraphQLError("Invalid or expired token.") from err
        except ValueError as err:
            raise GraphQLError("Invalid or expired token.") from err

        firebase_uid = decoded.get("uid")
        if not firebase_uid:
            raise GraphQLError("Invalid or expired token.")
        user = db["users"].find_one({"firebase_uid": firebase_uid})
        if not user:
            raise GraphQLError("User not found.")
        identity = str(user["_id"])
        return LoginUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
        )
