from flask_jwt_extended import get_jwt_identity
from graphene import ObjectType, String, Field, List
from graphql import GraphQLError
from src.services.user_service import UserService
from src.services.article_service import ArticleService
from src.services.youtube_video_service import YoutubeVideoService
from src.types import HighlightType, YoutubeVideoType
from src.utils.graphql_errors import graphql_jwt_required

class YoutubeVideoQuery(ObjectType):
    youtube_videos = List(YoutubeVideoType)
    youtube_video = Field(YoutubeVideoType, id=String(required=True))
    my_bookmarked_highlights = List(HighlightType)

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

    @graphql_jwt_required()
    def resolve_my_bookmarked_highlights(self, info):
        user = UserService.require_user(get_jwt_identity())
        if not user:
            raise GraphQLError("User not found.")
        highlights = []
        for highlight_id in user.bookmarked_highlight_ids:
            video = YoutubeVideoService.get_video_by_id(highlight_id)
            if video:
                highlights.append(video)
                continue

            article = ArticleService.get_article_by_id(highlight_id)
            if article:
                highlights.append(article)

        return highlights
