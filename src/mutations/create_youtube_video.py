from graphene import Mutation, String, Field
from src.types import YoutubeVideoType
from src.services.youtube_video_service import YoutubeVideoService

class CreateYoutubeVideo(Mutation):
    class Arguments:
        id = String(required=True)
        title = String(required=True)
        description = String(required=True)
        thumbnail = String(required=True)
        b64_thumbnail = String(required=True)
        url = String(required=True)
        published_at = String(required=True)
        duration = String(required=True)

    youtube_video = Field(lambda: YoutubeVideoType)

    def mutate(self, info, id, title, description, thumbnail, b64_thumbnail, url, published_at, duration):
        video_data = {
            "id": id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "b64_thumbnail": b64_thumbnail,
            "url": url,
            "published_at": published_at,
            "duration": duration,
        }
        new_video = YoutubeVideoService.create_video(video_data)
        return CreateYoutubeVideo(youtube_video=new_video)