from graphene import ObjectType, Schema, Mutation
from src.mutations import CreateGame, CreateTeam, CreateYoutubeVideo, CreateArticle
from src.queries import GameQuery, TeamQuery, YoutubeVideoQuery, ArticleQuery

class Query(TeamQuery, GameQuery, YoutubeVideoQuery, ArticleQuery, ObjectType):
    pass

class Mutation(ObjectType):
    create_game = CreateGame.Field(description="Creates a new game.")
    create_team = CreateTeam.Field(description="Creates a new team.")
    create_youtube_video = CreateYoutubeVideo.Field(description="Creates a new youtube video.")
    create_article = CreateArticle.Field(description="Creates a new article.")

schema = Schema(query=Query, mutation=Mutation)
