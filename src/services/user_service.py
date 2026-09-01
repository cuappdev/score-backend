from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService:
    @staticmethod
    def create_user(firebase_uid, email, name=None):
        return UserRepository.insert(
            User(firebase_uid=firebase_uid, email=email, name=name)
        )

    @staticmethod
    def get_user_by_firebase_uid(firebase_uid):
        return UserRepository.find_by_firebase_uid(firebase_uid)

    @staticmethod
    def get_user_by_id(user_id):
        return UserRepository.find_by_id(user_id)

    @staticmethod
    def require_user(user_id):
        return UserRepository.find_by_id(user_id)

    @staticmethod
    def add_favorite_game(user_id, game_id):
        return UserRepository.add_favorite_game(user_id, game_id)

    @staticmethod
    def remove_favorite_game(user_id, game_id):
        return UserRepository.remove_favorite_game(user_id, game_id)

    @staticmethod
    def get_favorite_game_ids(user_id):
        user = UserRepository.find_by_id(user_id)
        return user.favorite_game_ids if user else []
