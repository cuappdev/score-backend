from flask_jwt_extended import get_jwt_identity
from graphene import Field, ObjectType

from src.services.user_service import UserService
from src.types import UserType
from src.utils.graphql_errors import coded_error, graphql_jwt_required


class UserQuery(ObjectType):
    me = Field(UserType, required=True)

    @graphql_jwt_required()
    def resolve_me(self, info):
        user = UserService.get_user_by_id(get_jwt_identity())
        if not user:
            raise coded_error("Authentication required.", "UNAUTHENTICATED")
        return user
