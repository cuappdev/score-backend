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
