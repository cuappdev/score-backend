import requests
from src.utils.constants import CHANNEL_ID, VIDEO_LIMIT
from dotenv import load_dotenv
from src.models.youtube_video import YoutubeVideo
from src.services.youtube_video_service import YoutubeVideoService
from src.database import db
import base64
import os
import html

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
UPLOAD_URL = os.getenv("UPLOAD_URL")
DEV_BUCKET = os.getenv("DEV_BUCKET")
PROD_BUCKET = os.getenv("PROD_BUCKET")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def upload_image_to_bucket(image_b64: str) -> str:
    """
    Uploads a b64 image to the configured bucket and returns the URL of the uploaded image.
    """
    if ENVIRONMENT.lower() == "development":
        bucket = DEV_BUCKET
    else:
        bucket = PROD_BUCKET
    payload = {
         "bucket": bucket,
         "image": image_b64,
    }
    try:
        response = requests.post(UPLOAD_URL, data=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("url")
    except Exception as e:
        print(f"Error uploading image: {e}")
        raise

def fetch_videos():
    """
    Fetches the latest videos from the YouTube API and stores them in the database.
    """
    url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults={VIDEO_LIMIT}"
    response = requests.get(url)
    data = response.json()

    for item in data.get("items", []):
        if item.get("id", {}).get("kind") != "youtube#video":
            continue
        process_video_item(item)

def process_video_item(item):
    """
    Extracts the required data from a video item and
    passes it to be stored in the database.
    """

    video_id = item["id"]["videoId"]

    # video metadata
    snippet = item["snippet"]    
    title = html.unescape(snippet.get("title"))
    description = html.unescape(snippet.get("description"))

    thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url")
    # if high quality thumbnail is not available, use the default thumbnail
    if not thumbnail:
        thumbnail = snippet.get("thumbnails", {}).get("default", {}).get("url")

    uploaded_thumbnail_url = None  
    if thumbnail:
        try:
            thumb_response = requests.get(thumbnail)
            thumb_response.raise_for_status()
            encoded_thumbnail = base64.b64encode(thumb_response.content).decode('utf-8')
            uploaded_thumbnail_url = upload_image_to_bucket(encoded_thumbnail)
        except Exception as e:
            print(f"Error processing thumbnail: {e}")
    
    published_at = snippet.get("publishedAt")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    video_data = {
        "id": video_id, # use video id for easy retrieval
        "title": title,
        "description": description,
        "thumbnail": thumbnail,
        "b64_thumbnail": encoded_thumbnail,
        "url": video_url,
        "published_at": published_at,
    }
    process_video_data(video_data)


def process_video_data(video_data):
    """
    Adds Youtube video data to the database if it doesn't already exist.
    """
    existing_video = YoutubeVideoService.get_video_by_id(video_data["id"])
    if existing_video:
        return

    YoutubeVideoService.create_video(video_data)