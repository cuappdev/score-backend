from graphene import ObjectType, String, Field, List, Int
from src.services.game_service import GameService
from src.services.live_game_service import LiveGameService
from src.types import GameType


class GameQuery(ObjectType):
    games = List(
        GameType,
        limit=Int(default_value=100, description="Number of games to return"),
        offset=Int(default_value=0, description="Number of games to skip"),
    )
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
    games_by_sport = List(GameType, sport=String(required=True))
    games_by_gender = List(GameType, gender=String(required=True))
    games_by_sport_gender = List(
        GameType, sport=String(required=True), gender=String(required=True)
    )
    live_games = List(GameType, description="Get all currently live games")

    def resolve_games(self, info, limit=100, offset=0):
        """
        Resolver for retrieving all games with pagination.
        """
        return GameService.get_all_games(limit=limit, offset=offset)

    def resolve_game(self, info, id):
        """
        Resolver for retrieving a specific game by ID.
        """
        return GameService.get_game_by_id(id)

    def resolve_game_by_data(
        self, info, city, date, gender, opponent_id, sport, state, time, location=None
    ):
        """
        Resolver for retrieving a game by its data.
        """
        return GameService.get_game_by_data(
            city, date, gender, location, opponent_id, sport, state, time
        )

    def resolve_games_by_sport(self, info, sport):
        """
        Resolver for retrieving all games by its sport.
        """
        return GameService.get_games_by_sport(sport)

    def resolve_games_by_gender(self, info, gender):
        """
        Resolver for retrieving all games by its gender.
        """
        return GameService.get_games_by_gender(gender)

    def resolve_games_by_sport_gender(self, info, sport, gender):
        """
        Resolver for retrieving all games by its sport and gender.
        """
        return GameService.get_games_by_sport_gender(sport, gender)
    
    def resolve_live_games(self, info):
        """
        Resolver for retrieving all currently live games.
        """
        return LiveGameService.get_active_games()
