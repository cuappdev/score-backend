from src.database import db
from src.models.youtube_video import YoutubeVideo


class YoutubeVideoRepository:
    @staticmethod
    def find_all():
        """
        Retrieve all YouTube videos from the MongoDB collection.
        """
        collection = db["youtubevideo"]
        videos = collection.find()
        return [YoutubeVideo.from_dict(video) for video in videos]

    @staticmethod
    def find_by_id(video_id):
        """
        Retrieve a YouTube video by its ID.
        """
        collection = db["youtubevideo"]
        video_data = collection.find_one({"_id": video_id})
        return YoutubeVideo.from_dict(video_data) if video_data else None

    @staticmethod
    def insert(video):
        """
        Inserts a new YouTube video into the MongoDB collection.
        """
        collection = db["youtubevideo"]
        collection.insert_one(video.to_dict())

    @staticmethod
    def update_by_id(video_id, data):
        """
        Updates an existing YouTube video in the MongoDB collection.
        """
        collection = db["youtubevideo"]
        collection.update_one({"_id": video_id}, {"$set": data})

    @staticmethod
    def delete_by_id(video_id):
        """
        Deletes a YouTube video from the MongoDB collection.
        """
        collection = db["youtubevideo"]
        collection.delete_one({"_id": video_id})
