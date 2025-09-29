from src.repositories.game_repository import GameRepository
from src.models.game import Game
from src.services.team_service import TeamService


class GameService:
    @staticmethod
    def get_all_games(limit=100, offset=0):
        """
        Retrieves all games with pagination.

        Args:
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip

        Returns:
            list: A list of game documents
        """
        return GameRepository.find_all(limit=limit, offset=offset)

    @staticmethod
    def get_game_by_id(game_id):
        """
        Retrieve a game by its ID.
        """
        return GameRepository.find_by_id(game_id)

    @staticmethod
    def create_game(data):
        """
        Create a new game.
        """
        opponent_id = data.get("opponent_id")
        if not TeamService.get_team_by_id(opponent_id):
            raise ValueError(f"Opponent team with id {opponent_id} does not exist.")
        game = Game(**data)
        GameRepository.insert(game)
        return game

    @staticmethod
    def delete_game(game_id):
        """
        Delete a game by its ID.
        """
        GameRepository.delete_by_id(game_id)

    @staticmethod
    def update_game(game_id, data):
        """
        Update a game by its ID.
        """
        GameRepository.update_by_id(game_id, data)

    @staticmethod
    def get_game_by_data(city, date, gender, location, opponent_id, sport, state, time):
        """
        Retrieve a game by its data.
        """
        return GameRepository.find_by_data(
            city, date, gender, location, opponent_id, sport, state, time
        )

    @staticmethod
    def get_game_by_key_fields(city, date, gender, location, opponent_id, sport, state):
        """
        Retrieve a game by its essential fields, ignoring time
        """
        return GameRepository.find_by_key_fields(
            city, date, gender, location, opponent_id, sport, state
        )

    @staticmethod
    def get_games_by_sport(sport):
        """
        Retrieves all game by its sport.
        """
        return GameRepository.find_by_sport(sport)

    @staticmethod
    def get_games_by_gender(gender):
        """
        Retrieves all games by its gender.
        """
        return GameRepository.find_by_gender(gender)

    @staticmethod
    def get_games_by_sport_gender(sport, gender):
        """
        Retrieves all game by its sport and gender.
        """
        return GameRepository.find_by_sport_gender(sport, gender)
