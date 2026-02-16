from datetime import datetime, timezone

from graphene import Mutation, Boolean

from flask_jwt_extended import get_jwt, jwt_required
from src.database import db


class LogoutUser(Mutation):
    success = Boolean()

    @jwt_required(verify_type=False)
    def mutate(self, info):
        token = get_jwt()
        jti = token["jti"]
        exp = token["exp"]
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        db["token_blocklist"].insert_one({"jti": jti, "expires_at": expires_at})
        return LogoutUser(success=True)
