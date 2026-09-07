from graphql import GraphQLError
from graphene import Field, Mutation, String

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import create_access_token, create_refresh_token
from pymongo.errors import DuplicateKeyError
from src.services.user_service import UserService
from src.types import UserType

_TOKEN_ERRORS = (
    firebase_auth.InvalidIdTokenError,
    firebase_auth.ExpiredIdTokenError,
    firebase_auth.RevokedIdTokenError,
    firebase_auth.UserDisabledError,
)


class SignupUser(Mutation):
    class Arguments:
        id_token = String(required=True, description="Google Firebase ID token from the client.")

    access_token = String()
    refresh_token = String()
    user = Field(UserType, required=True)

    def mutate(self, info, id_token):
        try:
            decoded = firebase_auth.verify_id_token(id_token, check_revoked=True)
        except _TOKEN_ERRORS as err:
            raise GraphQLError("Invalid or expired token.") from err
        except ValueError as err:
            raise GraphQLError("Invalid or expired token.") from err

        firebase_uid = decoded.get("uid")
        provider = decoded.get("firebase", {}).get("sign_in_provider")
        if not firebase_uid or provider != "google.com":
            raise GraphQLError("Google authentication required.")

        try:
            user = UserService.create_user(
                firebase_uid,
                decoded.get("email"),
                decoded.get("name"),
            )
        except DuplicateKeyError as err:
            raise GraphQLError("User already exists.") from err

        identity = str(user.id)
        return SignupUser(
            access_token=create_access_token(identity=identity),
            refresh_token=create_refresh_token(identity=identity),
            user=user,
        )
