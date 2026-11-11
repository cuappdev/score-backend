import logging
import os

from graphql import GraphQLError

from src.models.report import Report
from src.repositories.report_repository import ReportRepository


REPORT_ISSUES = frozenset(
    {
        "INACCURATE_SCORES",
        "WRONG_GAME_TIME",
        "MISSING_GAME",
        "OTHER",
    }
)


class ReportService:
    """Business logic for creating and managing anonymous reports."""

    @staticmethod
    def create_report(issue, sport=None, description=None):
        issue = (issue or "").strip().upper()
        sport = sport.strip() if sport else None
        description = description.strip() if description else None

        if issue not in REPORT_ISSUES:
            raise GraphQLError("Issue is not a valid report category.")
        if description and len(description) > 5000:
            raise GraphQLError("Report description is too long.")

        report = Report(
            issue=issue,
            sport=sport,
            description=description,
        )
        ReportRepository.insert(report)
        ReportService._mirror_to_google_sheet(report)
        return report

    @staticmethod
    def get_reports(limit=100, offset=0):
        limit = max(1, min(limit or 100, 100))
        offset = max(offset or 0, 0)
        return ReportRepository.find_all(limit=limit, offset=offset)

    @staticmethod
    def delete_report(report_id):
        report_id = str(report_id).strip()
        report = ReportRepository.find_by_id(report_id)
        if not report:
            raise GraphQLError("Report with the given ID does not exist.")
        ReportRepository.delete_by_id(report_id)
        ReportService._remove_from_google_sheet(report_id)
        return report

    @staticmethod
    def _mirror_to_google_sheet(report):
        """Best-effort sheet mirroring; the database remains the source of truth."""
        sheet_id = os.getenv("BUG_REPORT_SHEET_ID") or os.getenv("SHEET_KEY")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_PATH"
        )
        if not sheet_id or not credentials_path:
            return

        try:
            import gspread

            client = gspread.service_account(filename=credentials_path)
            sheet_name = os.getenv("BUG_REPORT_SHEET_NAME", "Bug Reports")
            worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
            worksheet.append_row(
                [
                    report.id,
                    report.issue,
                    report.sport or "",
                    report.description or "",
                    report.created_at.isoformat(),
                ]
            )
        except Exception:
            # A reporting submission should not fail because an external mirror is
            # unavailable. Log the failure without including the report body.
            logging.exception("Could not mirror report %s to Google Sheets", report.id)

    @staticmethod
    def _remove_from_google_sheet(report_id):
        """Best-effort removal from the optional Google Sheets mirror."""
        sheet_id = os.getenv("BUG_REPORT_SHEET_ID") or os.getenv("SHEET_KEY")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_PATH"
        )
        if not sheet_id or not credentials_path:
            return

        try:
            import gspread

            client = gspread.service_account(filename=credentials_path)
            sheet_name = os.getenv("BUG_REPORT_SHEET_NAME", "Bug Reports")
            worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
            try:
                cell = worksheet.find(str(report_id), in_column=1)
            except gspread.exceptions.CellNotFound:
                return
            if cell:
                worksheet.delete_rows(cell.row)
        except Exception:
            logging.exception("Could not remove report %s from Google Sheets", report_id)

