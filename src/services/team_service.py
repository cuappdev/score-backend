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
    def create_team(team_data):
        """
        Create a new team.
        """
        team = Team(**team_data)
        TeamRepository.insert(team)
        return team

    @staticmethod
    def get_team_by_id(team_id):
        """
        Retrieve a team by ID.
        """
        return TeamRepository.find_by_id(team_id)

    @staticmethod
    def delete_team(team_id):
        """
        Delete a team by ID.
        """
        TeamRepository.delete_by_id(team_id)

    @staticmethod
    def update_team(team_id, team_data):
        """
        Update a team by ID.
        """
        TeamRepository.update_by_id(team_id, team_data)

    @staticmethod
    def get_team_by_name(name):
        """
        Retrieve a team by name.
        """
        return TeamRepository.find_by_name(name)
