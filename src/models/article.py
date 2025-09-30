from bson.objectid import ObjectId
from datetime import datetime

class Article:
    """
    A model representing a news article.

    Attributes:
        - title: The title of the article
        - image: The filename of the article's main image
        - sports_type: The specific sport category
        - published_at: The publication date
        - url: The URL to the full article
        - slug: Unique identifier from the source
        - created_at: When the article was added to our DB
    """
    def __init__(self, title, sports_type, published_at, url, slug, image=None, id=None, created_at=None):
        self.id = id if id else str(ObjectId())
        self.title = title
        self.image = image
        self.sports_type = sports_type
        self.published_at = published_at
        self.url = url
        self.slug = slug
        self.created_at = created_at if created_at else datetime.now()

    def to_dict(self):
        """
        Converts the Article object to a dictionary format for MongoDB storage.
        """
        return {
            "_id": self.id,
            "title": self.title,
            "image": self.image,
            "sports_type": self.sports_type,
            "published_at": self.published_at,
            "url": self.url,
            "slug": self.slug,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data):
        """
        Converts a MongoDB document to an Article object.
        """
        return Article(
            id=data.get("_id"),
            title=data.get("title"),
            image=data.get("image"),
            sports_type=data.get("sports_type"),
            published_at=data.get("published_at"),
            url=data.get("url"),
            slug=data.get("slug"),
            created_at=data.get("created_at")
        )