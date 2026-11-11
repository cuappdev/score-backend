from flask_jwt_extended import get_jwt_identity
from graphene import ObjectType, String, Field, List
from graphql import GraphQLError
from src.services.user_service import UserService
from src.services.youtube_video_service import YoutubeVideoService
from src.types import YoutubeVideoType
from src.utils.graphql_errors import graphql_jwt_required

class YoutubeVideoQuery(ObjectType):
    youtube_videos = List(YoutubeVideoType, sport=String(), gender=String())
    youtube_video = Field(YoutubeVideoType, id=String(required=True))
    my_bookmarked_highlights = List(YoutubeVideoType)

    def resolve_youtube_videos(self, info, sport=None, gender=None):
        """
        Resolver for retrieving YouTube videos, optionally filtered by sport
        and gender.
        """
        return YoutubeVideoService.get_videos(sport, gender)

    def resolve_youtube_video(self, info, id):
        """
        Resolver for retrieving a YouTube video by its ID.
        """
        return YoutubeVideoService.get_video_by_id(id)

    @graphql_jwt_required()
    def resolve_my_bookmarked_highlights(self, info):
        user = UserService.require_user(get_jwt_identity())
        if not user:
            raise GraphQLError("User not found.")
        return YoutubeVideoService.get_videos_by_ids(user.bookmarked_highlight_ids)
