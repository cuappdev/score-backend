from graphene import Int, List, ObjectType

from src.services.report_service import ReportService
from src.types import ReportType
from src.utils.auth import require_admin
from src.utils.graphql_errors import graphql_jwt_required


class ReportQuery(ObjectType):
    """Admin-only read operations for anonymous Score reports."""

    reports = List(
        ReportType,
        limit=Int(default_value=100),
        offset=Int(default_value=0),
        description="Get submitted reports with pagination (admin only).",
    )
    @graphql_jwt_required()
    def resolve_reports(self, info, limit=100, offset=0):
        require_admin()
        return ReportService.get_reports(limit=limit, offset=offset)
