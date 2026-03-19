from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from graphene import ObjectType, Schema, Mutation
from src.database import db
from src.mutations import (
    CreateGame,
    CreateTeam,
    CreateYoutubeVideo,
    CreateArticle,
    LoginUser,
    SignupUser,
    RefreshAccessToken,
    LogoutUser,
    AddFavoriteGame,
    RemoveFavoriteGame,
)
from src.queries import GameQuery, TeamQuery, YoutubeVideoQuery, ArticleQuery


class Query(TeamQuery, GameQuery, YoutubeVideoQuery, ArticleQuery, ObjectType):
    pass


class Mutation(ObjectType):
    create_game = CreateGame.Field(description="Creates a new game.")
    create_team = CreateTeam.Field(description="Creates a new team.")
    create_youtube_video = CreateYoutubeVideo.Field(description="Creates a new youtube video.")
    create_article = CreateArticle.Field(description="Creates a new article.")
    login_user = LoginUser.Field(description="Login by net_id; returns access_token and refresh_token.")
    signup_user = SignupUser.Field(
        description="Create a new user by net_id; returns access_token and refresh_token (no separate login needed).",
    )
    refresh_access_token = RefreshAccessToken.Field(
        description="Exchange a valid refresh token (in Authorization header) for a new access_token.",
    )
    logout_user = LogoutUser.Field(
        description="Revoke the current token (access or refresh). Send token in Authorization header.",
    )
    add_favorite_game = AddFavoriteGame.Field(
        description="Add a game to the current user's favorites (requires auth).",
    )
    remove_favorite_game = RemoveFavoriteGame.Field(
        description="Remove a game from the current user's favorites (requires auth).",
    )


# auto_camelcase=True (default): GraphQL API uses camelCase (loginUser, accessToken, refreshToken, etc.)
schema = Schema(query=Query, mutation=Mutation, auto_camelcase=True)
