from src.repositories.game_repository import GameRepository
from src.models.game import Game
from src.services.team_service import TeamService


class GameService:
    @staticmethod
    def get_all_games():
        """
        Retrieve all games.
        """
        return GameRepository.find_all()

    @staticmethod
    def create_game(data):
        """
        Create a new game.
        """
        opponent_id = data.get("opponent_id")
        if not TeamService.get_team_by_id(opponent_id):
            print(f"Opponent team with id {opponent_id} does not exist.")
            raise ValueError(f"Opponent team with id {opponent_id} does not exist.")
        game = Game(**data)
        GameRepository.insert(game)
        return game

    @staticmethod
    def get_game_by_id(game_id):
        """
        Retrieve a game by its ID.
        """
        return GameRepository.find_by_id(game_id)
