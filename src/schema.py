from graphene import ObjectType, String, Field, List, Schema, Mutation
from src.models.game import Game
from src.models.team import Team
from src.types import TeamType, GameType


class Query(ObjectType):
    """
    Query to retrieve data from the database.
    """

    teams = List(TeamType)
    team = Field(TeamType, id=String(required=True))
    games = List(GameType)
    game = Field(GameType, id=String(required=True))

    def resolve_teams(self, info):
        return Team.get_all_teams()

    def resolve_team(self, info, id):
        return Team.get_team_by_id(id)

    def resolve_games(self, info):
        return Game.get_all_games()

    def resolve_game(self, info, id):
        return Game.get_game_by_id(id)


class CreateTeam(Mutation):
    """
    Mutation to create a new team.
    """

    class Arguments:
        color = String(required=True)
        image = String(required=True)
        name = String(required=True)

    team = Field(lambda: TeamType)

    def mutate(self, info, color, image, name):

        new_team = Team(color=color, image=image, name=name)
        print(new_team)
        Team.insert_team(new_team)
        print(new_team.to_dict())
        return CreateTeam(team=new_team)


class CreateGame(Mutation):
    """
    Mutation to create a new game.
    """

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
        if len(city) == 0:
            raise ValueError("City cannot be empty.")

        # TODO: Check for valid sport

        opponent_team = Team.get_team_by_id(opponent_id)
        if not opponent_team:
            raise ValueError(f"Opponent team with id {opponent_id} does not exist.")

        new_game = Game(
            city=city,
            date=date,
            gender=gender,
            opponent_id=opponent_id,
            sport=sport,
            state=state,
            time=time,
        )
        Game.insert_game(new_game)
        return CreateGame(game=new_game)


class Mutation(ObjectType):
    create_team = CreateTeam.Field(description="Creates a new team.")
    create_game = CreateGame.Field(description="Creates a new game.")


schema = Schema(query=Query, mutation=Mutation)
