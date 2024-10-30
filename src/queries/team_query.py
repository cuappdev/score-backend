from graphene import ObjectType, String, Field, List
from src.services.team_service import TeamService
from src.types import TeamType


class TeamQuery(ObjectType):
    teams = List(TeamType)
    team = Field(TeamType, id=String(required=True))
    team_by_name = Field(TeamType, name=String(required=True))

    def resolve_teams(self, info):
        """
        Resolver for retrieving all teams.
        """
        return TeamService.get_all_teams()

    def resolve_team(self, info, id):
        """
        Resolver for retrieving a team by ID.
        """
        return TeamService.get_team_by_id(id)

    def resolve_team_by_name(self, info, name):
        """
        Resolver for retrieving a team by name.
        """
        return TeamService.get_team_by_name(name)
