from src.database import db
from src.models.report import Report


class ReportRepository:
    """Persistence operations for user reports."""

    collection = db["reports"]

    @classmethod
    def insert(cls, report):
        cls.collection.insert_one(report.to_dict())
        return report

    @classmethod
    def find_all(cls, limit=100, offset=0):
        reports = (
            cls.collection.find()
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [Report.from_dict(report) for report in reports]

    @classmethod
    def find_by_id(cls, report_id):
        return Report.from_dict(cls.collection.find_one({"_id": report_id}))

    @classmethod
    def delete_by_id(cls, report_id):
        result = cls.collection.delete_one({"_id": report_id})
        return result.deleted_count > 0
