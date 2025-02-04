from graphene import Mutation, String, Field
from src.types import YoutubeVideoType
from src.services.youtube_video_service import YoutubeVideoService

class CreateYoutubeVideo(Mutation):
    class Arguments:
        id = String(required=True)
        title = String(required=True)
        description = String(required=True)
        thumbnail = String(required=True)
        url = String(required=True)
        published_at = String(required=True)

    youtube_video = Field(lambda: YoutubeVideoType)

    def mutate(self, info, id, title, description, thumbnail, url, published_at):
        video_data = {
            "id": id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "url": url,
            "published_at": published_at,
        }
        new_video = YoutubeVideoService.create_video(video_data)
        return CreateYoutubeVideo(youtube_video=new_video)