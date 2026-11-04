from graphene import Field, Mutation, String

from src.services.report_service import ReportService
from src.types import ReportType


class CreateReport(Mutation):
    class Arguments:
        issue = String(required=True)
        sport = String(required=False)
        description = String(required=False)

    report = Field(ReportType, required=True)

    def mutate(self, info, issue, sport=None, description=None):
        report = ReportService.create_report(
            issue=issue,
            sport=sport,
            description=description,
        )
        return CreateReport(report=report)


class DeleteReport(Mutation):
    class Arguments:
        report_id = String(required=True)

    report = Field(ReportType, required=True)

    def mutate(self, info, report_id):
        return DeleteReport(report=ReportService.delete_report(report_id))
