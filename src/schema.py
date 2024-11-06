from graphene import ObjectType, Schema, Mutation
from src.mutations import CreateGame, CreateTeam
from src.queries import GameQuery, TeamQuery


class Query(TeamQuery, GameQuery, ObjectType):
    pass


class Mutation(ObjectType):
    create_game = CreateGame.Field(description="Creates a new game.")
    create_team = CreateTeam.Field(description="Creates a new team.")


schema = Schema(query=Query, mutation=Mutation)
