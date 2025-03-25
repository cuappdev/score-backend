from src.database import daily_sun_db
from src.models.article import Article
from src.repositories.article_repository import ArticleRepository
from datetime import datetime, timedelta
import logging

class ArticleService:
    @staticmethod
    def get_articles(sports_type=None):
        """
        Retrieve all articles from the last 3 days, optionally filtered by sports_type, sorted by published_at descending.
        """
        try:
            if sports_type:
                return ArticleRepository.find_by_sports_type(sports_type)
            return ArticleRepository.find_recent()
        except Exception as e:
            logging.error(f"Error retrieving articles: {str(e)}")
            return []

    @staticmethod
    def create_article(article_data):
        """
        Create a single article and store it in MongoDB.
        """
        try:
            article = Article(
                title=article_data["title"],
                sports_type=article_data["sports_type"],
                published_at=article_data["published_at"],
                url=article_data["url"],
                slug=article_data["slug"],
                image=article_data.get("image")
            )
            return ArticleRepository.upsert(article)
        except Exception as e:
            logging.error(f"Error creating article: {str(e)}")
            return None

    @staticmethod
    def create_articles_bulk(articles_data):
        """
        Create or update multiple articles in bulk and store them in MongoDB.
        """
        try:
            if not articles_data:
                return
            articles = [
                Article(
                    title=data["title"],
                    sports_type=data["sports_type"],
                    published_at=data["published_at"],
                    url=data["url"],
                    slug=data["slug"],
                    image=data.get("image")
                )
                for data in articles_data
            ]
            ArticleRepository.bulk_upsert(articles)
        except Exception as e:
            logging.error(f"Error creating articles in bulk: {str(e)}")
            raise

    @staticmethod
    def cleanse_old_articles():
        """
        Remove articles older than 3 days from the database.
        """
        try:
            ArticleRepository.delete_not_recent(limit_days=5) # provide a buffer from the 3-day threshold
        except Exception as e:
            logging.error(f"Error cleansing old articles: {str(e)}")
            raise