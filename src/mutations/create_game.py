from graphene import Mutation, String, Field
from src.types import GameType
from src.services import GameService


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

    def mutate(self, info, city, date, gender, opponent_id, sport, state, time):
        print("A")
        game_data = {
            "city": city,
            "date": date,
            "gender": gender,
            "opponent_id": opponent_id,
            "sport": sport,
            "state": state,
            "time": time,
        }
        print(game_data["city"])
        new_game = GameService.create_game(game_data)
        return CreateGame(game=new_game)
