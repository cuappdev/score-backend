from functools import wraps

from flask_jwt_extended import jwt_required
from flask_jwt_extended.exceptions import JWTExtendedException
from graphql import GraphQLError
from jwt import PyJWTError


def coded_error(message, code):
    return GraphQLError(message, extensions={"code": code})


def graphql_jwt_required(refresh=False, verify_type=True):
    """Apply JWT validation while returning a stable GraphQL error code."""

    def decorator(function):
        protected = jwt_required(refresh=refresh, verify_type=verify_type)(function)

        @wraps(function)
        def wrapped(*args, **kwargs):
            try:
                return protected(*args, **kwargs)
            except (JWTExtendedException, PyJWTError) as error:
                raise coded_error(
                    "Authentication required.", "UNAUTHENTICATED"
                ) from error

        return wrapped

    return decorator
