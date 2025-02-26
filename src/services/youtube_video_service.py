from src.repositories.youtube_video_repository import YoutubeVideoRepository
from src.models.youtube_video import YoutubeVideo


class YoutubeVideoService:
    @staticmethod
    def get_all_videos():
        """
        Retrieve all stored YouTube videos.
        """
        return YoutubeVideoRepository.find_all()

    @staticmethod
    def get_video_by_id(video_id):
        """
        Retrieve a YouTube video by its ID.
        """
        return YoutubeVideoRepository.find_by_id(video_id)

    @staticmethod
    def create_video(data):
        """
        Create a new YouTube video instance.
        """
        video = YoutubeVideo(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description"),
            thumbnail=data.get("thumbnail"),
            b64_thumbnail=data.get("b64_thumbnail"),
            url=data.get("url"),
            published_at=data.get("published_at"),
        )
        YoutubeVideoRepository.insert(video)
        return video

    @staticmethod
    def update_video(video_id, data):
        """
        Update a YouTube video by its ID.
        """
        YoutubeVideoRepository.update_by_id(video_id, data)

    @staticmethod
    def delete_video(video_id):
        """
        Delete a YouTube video by its ID.
        """
        YoutubeVideoRepository.delete_by_id(video_id)
