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
    def add_favorite_team(user_id, gender, sport):
        return UserRepository.add_favorite_team(user_id, gender, sport)

    @staticmethod
    def remove_favorite_team(user_id, gender, sport):
        return UserRepository.remove_favorite_team(user_id, gender, sport)

    @staticmethod
    def add_bookmarked_highlight(user_id, highlight_id):
        return UserRepository.add_bookmarked_highlight(user_id, highlight_id)

    @staticmethod
    def remove_bookmarked_highlight(user_id, highlight_id):
        return UserRepository.remove_bookmarked_highlight(user_id, highlight_id)
