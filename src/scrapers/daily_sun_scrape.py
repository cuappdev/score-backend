import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from ..services import ArticleService
from ..utils.constants import ARTICLE_IMG_TAG
from ..utils.helpers import extract_sport_type_from_title
import logging
from bs4 import BeautifulSoup
import base64

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

        # Current date and 3-day threshold (in UTC)
        current_date = datetime.now(timezone.utc)
        three_days_ago = current_date - timedelta(days=3)

        # Process articles
        articles_to_store = []
        for article in data.get("articles", []):
            published_at_dt = datetime.strptime(article["published_at"], "%Y-%m-%d %H:%M:%S")
            # Assume the timezone is UTC and convert to ISO 8601 format string
            published_at_dt = published_at_dt.replace(tzinfo=timezone.utc)
            published_at = published_at_dt.isoformat().replace('+00:00', 'Z')
            
            if published_at >= three_days_ago:
                # Extract sport type from title
                title = article["headline"]
                sports_type = extract_sport_type_from_title(title)
                article_url = f"https://cornellsun.com/article/{article['slug']}"

                article_image = None
                try:
                    response = requests.get(
                        article_url,
                        headers={
                            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                        }
                    )
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    img_tag = soup.select_one(ARTICLE_IMG_TAG)
                    if img_tag and img_tag.get('src'):
                        article_image=img_tag.get('src')
                except Exception as e:
                    logging.error(f"Error fetching news: {str(e)}")
                article_doc = {
                    "title": article["headline"],
                    "image": article_image,
                    "sports_type": sports_type,
                    "published_at": published_at,
                    "url": article_url,
                    "slug": article["slug"],
                    "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
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
