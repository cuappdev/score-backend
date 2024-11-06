from graphene import Mutation, String, Field
from src.types import TeamType
from src.services import TeamService


class CreateTeam(Mutation):
    class Arguments:
        color = String(required=True)
        image = String(required=False)
        name = String(required=True)

    team = Field(lambda: TeamType)

    def mutate(self, info, color, name, image=None):
        team_data = {"color": color, "image": image, "name": name}
        new_team = TeamService.create_team(team_data)
        return CreateTeam(team=new_team)
