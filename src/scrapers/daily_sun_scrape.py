import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ..services import ArticleService
import logging

load_dotenv()


def fetch_news():
    try:
        url = os.getenv("DAILY_SUN_URL")
        response = requests.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
        )
        response.raise_for_status()
        data = response.json()

        # Current date and 3-day threshold
        current_date = datetime.now()
        three_days_ago = current_date - timedelta(days=3)

        # Process articles
        articles_to_store = []
        for article in data.get("articles", []):
            published_at = datetime.strptime(article["published_at"], "%Y-%m-%d %H:%M:%S")
            
            if published_at >= three_days_ago:
                sports_type = next(
                    (tag["name"] for tag in article["tags"] if tag["name"] not in ["Sports", "Top Stories"]),
                    "General"
                )
                article_url = f"https://cornellsun.com/article/{article['slug']}"

                article_doc = {
                    "title": article["headline"],
                    "image": article["dominantMedia"]["title"] if article["dominantMedia"] else None,
                    "sports_type": sports_type,
                    "published_at": published_at,
                    "url": article_url,
                    "slug": article["slug"],
                    "created_at": datetime.now()
                }
                articles_to_store.append(article_doc)

        if articles_to_store:
            ArticleService.create_articles_bulk(articles_to_store)
            logging.info(f"Stored/Updated {len(articles_to_store)} recent articles")
        else:
            logging.info("No recent articles to store")
        return True

    except Exception as e:
        logging.error(f"Error fetching news: {str(e)}")
        return False
