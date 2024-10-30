from graphene import ObjectType, String, Field, List
from src.services.team_service import TeamService
from src.types import TeamType


class TeamQuery(ObjectType):
    teams = List(TeamType)
    team = Field(TeamType, id=String(required=True))

    def resolve_teams(self, info):
        return TeamService.get_all_teams()

    def resolve_team(self, info, id):
        return TeamService.get_team_by_id(id)
