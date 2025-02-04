from graphene import ObjectType, String, Field, List
from src.services.youtube_video_service import YoutubeVideoService
from src.types import YoutubeVideoType

class YoutubeVideoQuery(ObjectType):
    youtube_videos = List(YoutubeVideoType)
    youtube_video = Field(YoutubeVideoType, id=String(required=True))

    def resolve_youtube_videos(self, info):
        """
        Resolver for retrieving all YouTube videos.
        """
        return YoutubeVideoService.get_all_videos()

    def resolve_youtube_video(self, info, id):
        """
        Resolver for retrieving a YouTube video by its ID.
        """
        return YoutubeVideoService.get_video_by_id(id)