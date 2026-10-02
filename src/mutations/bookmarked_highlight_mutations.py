from graphql import GraphQLError
from graphene import Boolean, Mutation, String

from flask_jwt_extended import get_jwt_identity
from src.services.user_service import UserService
from src.services.youtube_video_service import YoutubeVideoService
from src.utils.graphql_errors import graphql_jwt_required


class AddBookmarkedHighlight(Mutation):
    class Arguments:
        highlight_id = String(
            required=True,
            description="ID of the highlight to bookmark.",
        )

    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, highlight_id):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        if not highlight_id.strip():
            raise GraphQLError("Highlight ID is required.")
        if not YoutubeVideoService.get_video_by_id(highlight_id):
            raise GraphQLError("Highlight not found.")
        if not UserService.add_bookmarked_highlight(user_id, highlight_id):
            raise GraphQLError("Could not bookmark highlight.")
        return AddBookmarkedHighlight(success=True)


class RemoveBookmarkedHighlight(Mutation):
    class Arguments:
        highlight_id = String(
            required=True,
            description="ID of the highlight to remove from bookmarks.",
        )

    success = Boolean()

    @graphql_jwt_required()
    def mutate(self, info, highlight_id):
        user_id = get_jwt_identity()
        if not UserService.require_user(user_id):
            raise GraphQLError("User not found.")
        if not highlight_id.strip():
            raise GraphQLError("Highlight ID is required.")
        if not YoutubeVideoService.get_video_by_id(highlight_id):
            raise GraphQLError("Highlight not found.")
        if not UserService.remove_bookmarked_highlight(user_id, highlight_id):
            raise GraphQLError("Could not remove highlight bookmark.")
        return RemoveBookmarkedHighlight(success=True)
