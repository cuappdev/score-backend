from datetime import datetime, timezone

from bson.objectid import ObjectId


class Report:
    """An anonymous bug or data-quality report."""

    def __init__(
        self,
        issue,
        sport=None,
        description=None,
        id=None,
        created_at=None,
    ):
        self.id = str(id) if id is not None else str(ObjectId())
        self.issue = issue
        self.sport = sport
        self.description = description
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self):
        """Convert the report to a MongoDB document."""
        return {
            "_id": self.id,
            "issue": self.issue,
            "sport": self.sport,
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Convert a MongoDB document to a report."""
        if not data:
            return None
        return cls(
            id=data.get("_id"),
            issue=data.get("issue"),
            sport=data.get("sport"),
            description=data.get("description"),
            created_at=data.get("created_at"),
        )
