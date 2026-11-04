from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def utc_now():
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


@dataclass
class User:
    """Application user linked to an identity managed by Firebase."""

    firebase_uid: Optional[str]
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    id: object = None

    def to_dict(self):
        document = {
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.id is not None:
            document["_id"] = self.id
        return document

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
        return cls(
            id=data.get("_id"),
            firebase_uid=data.get("firebase_uid"),
            email=data.get("email"),
            name=data.get("name"),
            created_at=data.get("created_at") or utc_now(),
            updated_at=data.get("updated_at") or utc_now(),
        )
