from src.repositories import TeamRepository
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
        Create a new team, or update it if it already exists.
        
        Args:
            team_data (dict): The data for the new team.
        Returns:
            Team: The created team.
        """
        name = team_data.get("name")
        if not name:
            raise ValueError("Team name is required to create a team.")
        
        existing = TeamService.get_team_by_name(name)
        if existing:
            if isinstance(existing, list) and existing:
                existing = existing[0]

            TeamService.update_team(existing.id, team_data)
            return existing

        team = Team(**team_data)
        TeamRepository.insert(team)
        return team

    @staticmethod
    def get_team_by_id(team_id):
        """
        Retrieve a team by ID.

        Args:
            team_id (str): The ID of the team to retrieve.

        Returns:
            Team: The retrieved team.
        """
        return TeamRepository.find_by_id(team_id)

    @staticmethod
    def delete_team(team_id):
        """
        Delete a team by ID.

        Args:
            team_id (str): The ID of the team to delete.
        """
        TeamRepository.delete_by_id(team_id)

    @staticmethod
    def update_team(team_id, team_data):
        """
        Update a team by ID.

        Args:
            team_id (str): The ID of the team to update.
            team_data (dict): The updated data for the team.
        """
        TeamRepository.update_by_id(team_id, team_data)

    @staticmethod
    def get_team_by_name(name):
        """
        Retrieve a team by name.

        Args:
            name (str): The name of the team to retrieve.

        Returns:
            Team: The retrieved team.
        """
        return TeamRepository.find_by_name(name)

    @staticmethod
    def get_teams_by_ids(team_ids):
        """
        Retrieve teams by a list of IDs.

        Args:
            team_ids (list): The list of team IDs to retrieve.

        Returns:
            list: The list of retrieved teams.
        """
        return TeamRepository.find_by_ids(team_ids)