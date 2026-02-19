from bson import ObjectId
from flask_jwt_extended import get_jwt_identity, jwt_required
from graphene import ObjectType, String, Field, List, Int, DateTime
from src.database import db
from src.services.game_service import GameService
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
    games_by_date = List(GameType, startDate=DateTime(required=True), endDate=DateTime(required=True))
    my_favorited_games = List(GameType, description="Current user's favorited games (requires auth).")

    @jwt_required()
    def resolve_my_favorited_games(self, info):
        user_id = get_jwt_identity()
        user = db["users"].find_one({"_id": ObjectId(user_id)})
        if not user:
            return []
        favorite_ids = user.get("favorite_game_ids") or []
        if not favorite_ids:
            return []
        return GameService.get_games_by_ids(favorite_ids)

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
    
    def resolve_games_by_date(self, info, startDate, endDate):
        """
        Resolver for retrieving games by date.
        """
        return GameService.get_games_by_date(startDate, endDate)
