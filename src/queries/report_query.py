from graphene import Int, List, ObjectType

from src.services.report_service import ReportService
from src.types import ReportType


class ReportQuery(ObjectType):
    """Read operations for anonymous Score reports."""

    reports = List(
        ReportType,
        limit=Int(default_value=100),
        offset=Int(default_value=0),
        description="Get submitted reports with pagination.",
    )
    get_all_reports = List(
        ReportType,
        limit=Int(default_value=100),
        offset=Int(default_value=0),
        description="Get submitted reports with pagination.",
    )

    def resolve_reports(self, info, limit=100, offset=0):
        return ReportService.get_reports(limit=limit, offset=offset)

    def resolve_get_all_reports(self, info, limit=100, offset=0):
        return ReportService.get_reports(limit=limit, offset=offset)
