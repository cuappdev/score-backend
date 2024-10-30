from src.repositories.team_repository import TeamRepository
from src.models.team import Team


class TeamService:
    @staticmethod
    def get_all_teams():
        """
        Retrieve all teams.
        """
        return TeamRepository.find_all()

    @staticmethod
    def get_team_by_id(team_id):
        """
        Retrieve a team by ID.
        """
        return TeamRepository.find_by_id(team_id)

    @staticmethod
    def create_team(team_data):
        """
        Create a new team.
        """
        team = Team(**team_data)
        TeamRepository.insert(team)
        return team
