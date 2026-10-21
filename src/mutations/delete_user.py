from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from flask_jwt_extended import get_jwt, get_jwt_identity
from graphene import Boolean, Mutation
from graphql import GraphQLError

from src.database import db
from src.services.user_service import UserService
from src.utils.graphql_errors import graphql_jwt_required


class DeleteUser(Mutation):
    """Permanently delete the authenticated user's application and Firebase accounts."""

    success = Boolean(required=True)

    @graphql_jwt_required(verify_type=False)
    def mutate(self, info):
        user_id = get_jwt_identity()
        user = UserService.require_user(user_id)
        if not user:
            raise GraphQLError("User not found.")
        if not user.firebase_uid:
            raise GraphQLError("User is not linked to a Firebase account.")

        try:
            firebase_auth.delete_user(user.firebase_uid)
        except firebase_auth.UserNotFoundError:
            # Continue deleting local data when the Firebase account was already removed.
            pass
        except Exception as error:
            raise GraphQLError("Could not delete Firebase account.") from error

        if not UserService.delete_user(user_id):
            raise GraphQLError("Could not delete application account.")

        # Revoke the token that performed the deletion so it cannot be reused.
        token = get_jwt()
        db["token_blocklist"].insert_one(
            {
                "jti": token["jti"],
                "expires_at": datetime.fromtimestamp(token["exp"], tz=timezone.utc),
            }
        )

        return DeleteUser(success=True)
