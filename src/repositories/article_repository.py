from src.database import daily_sun_db
from src.models.article import Article
from pymongo import UpdateOne
from datetime import datetime, timedelta

class ArticleRepository:
    @staticmethod
    def upsert(article):
        """
        Upsert an article into the 'news_articles' collection in MongoDB.
        """
        article_collection = daily_sun_db["news_articles"]
        article_dict = article.to_dict()
        # Remove _id from the update to avoid MongoDB error
        article_dict.pop("_id", None)
        
        article_collection.update_one(
            {"slug": article.slug},
            {"$set": article_dict},
            upsert=True
        )

    @staticmethod
    def bulk_upsert(articles):
        """
        Bulk upsert articles into the 'news_articles' collection based on slug.
        """
        if not articles:
            return

        article_collection = daily_sun_db["news_articles"]
        operations = []
        for article in articles:
            article_dict = article.to_dict()
            # Remove _id from the update to avoid MongoDB error
            article_dict.pop("_id", None)
            
            operations.append(
                UpdateOne(
                    {"slug": article.slug},
                    {"$set": article_dict},
                    upsert=True
                )
            )
        
        if operations:
            article_collection.bulk_write(operations)

    @staticmethod
    def find_recent(limit_days=3):
        """
        Retrieve articles from the last N days, sorted by published_at descending.
        """
        article_collection = daily_sun_db["news_articles"]
        query = {"published_at": {"$gte": datetime.now() - timedelta(days=limit_days)}}
        articles = article_collection.find(query).sort("published_at", -1)
        return [Article.from_dict(article) for article in articles]

    @staticmethod
    def find_by_sports_type(sports_type, limit_days=3):
        """
        Retrieve articles by sports_type from the last N days, sorted by published_at descending.
        """
        article_collection = daily_sun_db["news_articles"]
        query = {
            "sports_type": sports_type,
            "published_at": {"$gte": datetime.now() - timedelta(days=limit_days)}
        }
        articles = article_collection.find(query).sort("published_at", -1)
        return [Article.from_dict(article) for article in articles]
    
    @staticmethod
    def delete_not_recent(limit_days=3):
        """
        Delete articles older than N days, sorted by published_at descending.
        """
        article_collection = daily_sun_db["news_articles"]
        query = {"published_at": {"$lt": datetime.now() - timedelta(days=limit_days)}}
        article_collection.delete_many(query)