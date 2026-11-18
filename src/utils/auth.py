import os

from flask_jwt_extended import get_jwt_identity

from src.services.user_service import UserService
from src.utils.graphql_errors import coded_error


def require_admin():
    """Require a valid backend JWT belonging to an allowlisted admin email."""
    user = UserService.get_user_by_id(get_jwt_identity())

    if not user:
        raise coded_error("Authentication required.", "UNAUTHENTICATED")

    admin_emails = {
        email.strip().casefold()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }

    if not user.email or user.email.casefold() not in admin_emails:
        raise coded_error("Admin access required.", "FORBIDDEN")

    return user
