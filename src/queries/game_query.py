from graphene import ObjectType, String, Field, List
from src.services.game_service import GameService
from src.types import GameType


class GameQuery(ObjectType):
    games = List(GameType)
    game = Field(GameType, id=String(required=True))
    game_by_data = Field(
        GameType,
        city=String(required=True),
        date=String(required=True),
        gender=String(required=True),
        location=String(required=False),
        opponent_id=String(required=True),
        sport=String(required=True),
        state=String(required=True),
        time=String(required=True),
    )

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

    def resolve_game_by_data(
        self, info, city, date, gender, opponent_id, sport, state, time, location=None
    ):
        return GameService.get_game_by_data(
            city, date, gender, location, opponent_id, sport, state, time
        )
