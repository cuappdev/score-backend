import requests
from src.utils.constants import CHANNEL_ID, VIDEO_LIMIT
from dotenv import load_dotenv
from src.models.youtube_video import YoutubeVideo
from src.services.youtube_video_service import YoutubeVideoService
import base64
import os
import html
from bs4 import BeautifulSoup

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


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


def get_video_duration(video_id):
    """
    Gets video duration using YouTube API
    """
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={video_id}&part=contentDetails"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get("items"):
            duration_iso = data["items"][0]["contentDetails"]["duration"]
            return convert_iso_duration(duration_iso)
        return None
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None


def convert_iso_duration(iso_duration):
    """
    Converts ISO 8601 duration (PT2M5S) to readable format (2:05)
    Examples:
    - PT2M5S -> 2:05
    - PT1H23M45S -> 1:23:45
    - PT30S -> 0:30
    """
    import re
    
    # Remove PT prefix
    duration = iso_duration.replace('PT', '')
    
    # Extract hours, minutes, seconds
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    seconds = re.search(r'(\d+)S', duration)
    
    h = int(hours.group(1)) if hours else 0
    m = int(minutes.group(1)) if minutes else 0
    s = int(seconds.group(1)) if seconds else 0
    
    # Format as MM:SS or HH:MM:SS
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m}:{s:02d}"


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

    encoded_thumbnail = None
    if thumbnail:
        try:
            response = requests.get(thumbnail)
            response.raise_for_status()
            encoded_thumbnail = base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            print(f"Error fetching thumbnail: {e}")

    published_at = snippet.get("publishedAt")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    duration = get_video_duration(video_id)

    video_data = {
        "id": video_id,  
        "title": title,
        "description": description,
        "thumbnail": thumbnail,
        "b64_thumbnail": encoded_thumbnail,
        "url": video_url,
        "published_at": published_at,
        "duration": duration,
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
