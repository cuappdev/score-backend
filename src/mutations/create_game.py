from graphene import Mutation, String, Field
from src.types import GameType
from src.services import GameService


class CreateGame(Mutation):
    class Arguments:
        city = String(required=True)
        date = String(required=True)
        gender = String(required=True)
        location = String(required=False)
        opponent_id = String(required=True)
        result = String(required=False)
        sport = String(required=True)
        state = String(required=True)
        time = String(required=True)

    game = Field(lambda: GameType)

    def mutate(
        self,
        info,
        city,
        date,
        gender,
        opponent_id,
        sport,
        state,
        location=None,
        result=None,
        time=None,
    ):
        game_data = {
            "city": city,
            "date": date,
            "gender": gender,
            "location": location,
            "opponent_id": opponent_id,
            "result": result,
            "sport": sport,
            "state": state,
            "time": time,
        }
        new_game = GameService.create_game(game_data)
        return CreateGame(game=new_game)
