from graphene import ObjectType, String, Field, List, Schema, Mutation
from src.models.game import Game
from src.models.team import Team
from src.types import GameType


class Query(ObjectType):
    games = List(GameType)

    def resolve_games(self, info):
        return Game.get_all_games()


class CreateGame(Mutation):
    class Arguments:
        city = String(required=True)
        date = String(required=True)
        gender = String(required=True)
        opponent_id = String(required=True)
        sport = String(required=True)
        state = String(required=True)
        time = String(required=True)

    game = Field(lambda: GameType)

    def mutate(self, info, _id, city, date, gender, opponent_id, sport, state, time):

        new_game = Game(
            _id=_id,
            city=city,
            date=date,
            gender=gender,
            opponent_id=opponent_id,
            sport=sport,
            state=state,
            time=time,
        )
        Game.insert_book(new_game)
        return Game(
            game=GameType(
                _id=new_game.id,
                city=new_game.city,
                date=new_game.date,
                gender=new_game.gender,
                opponent_id=new_game.opponent_id,
                sport=new_game.sport,
                state=new_game.state,
                time=new_game.time,
            )
        )


class Mutation(ObjectType):
    create_game = CreateGame.Field(description="Creates a new game.")


schema = Schema(query=Query, mutation=Mutation)
