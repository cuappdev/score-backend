from graphene import ObjectType, String, Field, List
from src.services.game_service import GameService
from src.types import GameType


class GameQuery(ObjectType):
    games = List(GameType)
    game = Field(GameType, id=String(required=True))

    def resolve_games(self, info):
        """
        Resolver for retrieving all games.
        """
        return GameService.get_all_games()

    def resolve_game(self, info, id):
        """
        Resolver for retrieving a specific game by ID.
        """
        return GameService.get_game_by_id(id)
