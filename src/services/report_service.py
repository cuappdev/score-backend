from concurrent.futures import ThreadPoolExecutor
import logging
import os
from threading import Lock

from graphql import GraphQLError

from src.models.report import Report
from src.repositories.report_repository import ReportRepository
from src.utils.constants import (
    DEFAULT_REPORT_SHEET_NAME,
    MAX_REPORT_DESCRIPTION_LENGTH,
)


REPORT_ISSUES = frozenset(
    {
        "INACCURATE_SCORES",
        "WRONG_GAME_TIME",
        "MISSING_GAME",
        "OTHER",
    }
)

# Keep Google Sheets work bounded so anonymous report submissions cannot create
# an unbounded number of background threads.
REPORT_SHEET_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="report-sheet",
)


class ReportService:
    """Business logic for creating and managing anonymous reports."""

    _google_sheet_client = None
    _google_sheet_worksheet = None
    _google_sheet_cache_key = None
    _google_sheet_cache_lock = Lock()

    @staticmethod
    def create_report(issue, sport=None, description=None):
        issue = (issue or "").strip().upper()
        sport = sport.strip() if sport else None
        description = description.strip() if description else None

        if issue not in REPORT_ISSUES:
            raise GraphQLError("Issue is not a valid report category.")
        if description and len(description) > MAX_REPORT_DESCRIPTION_LENGTH:
            raise GraphQLError("Report description is too long.")

        report = Report(
            issue=issue,
            sport=sport,
            description=description,
        )
        ReportRepository.insert(report)
        ReportService._mirror_to_google_sheet_async(report)
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
        try:
            worksheet = ReportService._get_worksheet()
            if worksheet is None:
                return
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
    def _get_worksheet():
        """Return the configured worksheet, reusing its authenticated client."""
        sheet_id = os.getenv("BUG_REPORT_SHEET_ID") or os.getenv("SHEET_KEY")
        # Keep Sheets access separate from the Firebase Admin credentials.
        credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        if not sheet_id or not credentials_path:
            return None

        sheet_name = os.getenv("BUG_REPORT_SHEET_NAME", DEFAULT_REPORT_SHEET_NAME)
        cache_key = (sheet_id, credentials_path, sheet_name)
        with ReportService._google_sheet_cache_lock:
            if cache_key != ReportService._google_sheet_cache_key:
                import gspread

                client = gspread.service_account(filename=credentials_path)
                worksheet = client.open_by_key(sheet_id).worksheet(sheet_name)
                ReportService._google_sheet_client = client
                ReportService._google_sheet_worksheet = worksheet
                ReportService._google_sheet_cache_key = cache_key

            return ReportService._google_sheet_worksheet

    @staticmethod
    def _mirror_to_google_sheet_async(report):
        """Queue sheet mirroring so report creation is not blocked by Google."""
        try:
            REPORT_SHEET_EXECUTOR.submit(ReportService._mirror_to_google_sheet, report)
        except RuntimeError:
            # The executor may be shutting down during process termination. The
            # database write has already succeeded, so log and leave it intact.
            logging.exception("Could not queue report %s for Google Sheets", report.id)

    @staticmethod
    def _remove_from_google_sheet(report_id):
        """Best-effort removal from the optional Google Sheets mirror."""
        try:
            worksheet = ReportService._get_worksheet()
            if worksheet is None:
                return
            cells = worksheet.findall(str(report_id), in_column=1)
            if cells:
                worksheet.delete_rows(cells[0].row)
        except Exception:
            logging.exception("Could not remove report %s from Google Sheets", report_id)

