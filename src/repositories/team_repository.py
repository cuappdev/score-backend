import re
from src.database import db
from src.models.team import Team
from bson.objectid import ObjectId


class TeamRepository:
    @staticmethod
    def find_all():
        """
        Retrieve all teams from the 'team' collection in MongoDB.

        Returns:
            List[Team]: A list of Team objects.
        """
        team_collection = db["team"]
        teams = team_collection.find()
        return [Team.from_dict(team) for team in teams]

    @staticmethod
    def insert(team):
        """
        Inserts a new team into the 'team' collection in MongoDB.

        Args:
            team (Team): The Team object to insert.
        """
        team_collection = db["team"]
        team_collection.insert_one(team.to_dict())

    @staticmethod
    def find_by_id(team_id):
        """
        Fetch a team from the MongoDB collection by its ID.

        Args:
            team_id (str): The ID of the team to retrieve.

        Returns:
            Team: The retrieved team or None if not found.
        """
        team_collection = db["team"]
        team_data = team_collection.find_one({"_id": team_id})
        return Team.from_dict(team_data) if team_data else None

    @staticmethod
    def delete_by_id(team_id):
        """
        Delete a team from the MongoDB collection by its ID.

        Args:
            team_id (str): The ID of the team to delete.
        """
        team_collection = db["team"]
        team_collection.delete_one({"_id": team_id})

    @staticmethod
    def update_by_id(team_id, team_data):
        """
        Update a team in the MongoDB collection by its ID.

        Args:
            team_id (str): The ID of the team to update.
            team_data (dict): The updated data for the team.
        """
        team_collection = db["team"]
        team_collection.update_one({"_id": team_id}, {"$set": team_data})

    @staticmethod
    def find_by_name(name):
        """
        Fetch a team from the MongoDB collection by its name.

        Args:
            name (str): The name of the team to retrieve.

        Returns:
            Team: The retrieved team or None if not found.
        """
        team_collection = db["team"]
        team_data = team_collection.find_one({"name": name})
        return Team.from_dict(team_data) if team_data else None

    @staticmethod
    def find_by_name_containing(name, case_sensitive=False):
        """
        Fetch teams whose name contains the given substring.

        Args:
            name (str): The substring to search for in team names.
            case_sensitive (bool): If True, match case; default False.

        Returns:
            List[Team]: The list of matching teams.
        """
        if not name:
            return []
        team_collection = db["team"]
        pattern = re.escape(name)
        options = "" if case_sensitive else "i"
        cursor = team_collection.find({"name": {"$regex": pattern, "$options": options}})
        return [Team.from_dict(t) for t in cursor]

    @staticmethod
    def find_by_ids(team_ids):
        """
        Fetch a list of teams from the MongoDB collection by their IDs.

        Args:
            team_ids (List[str]): The IDs of the teams to retrieve.

        Returns:
            List[Team]: The retrieved teams.
        """
        team_collection = db["team"]
        team_data = team_collection.find({"_id": {"$in": team_ids}})
        return [Team.from_dict(team) for team in team_data]