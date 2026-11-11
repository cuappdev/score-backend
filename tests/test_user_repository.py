import sys
import types
from unittest.mock import Mock, patch

from pymongo import ReturnDocument


# Importing the repositories package initializes the real MongoDB client. Keep
# this unit test independent of that application startup side effect.
fake_database = types.ModuleType("src.database")
fake_database.db = {}
fake_database.daily_sun_db = {}
sys.modules.setdefault("src.database", fake_database)

from src.repositories.user_repository import UserRepository


def test_favorite_team_update_works_from_class_and_instance():
    updated_document = {
        "_id": "user-id",
        "firebase_uid": "firebase-uid",
        "favorite_teams": [{"gender": "Mens", "sport": "Soccer"}],
    }
    collection = Mock()
    collection.find_one_and_update.return_value = updated_document

    with patch("src.repositories.user_repository.db", {"users": collection}), patch(
        "src.repositories.user_repository.ObjectId", return_value="user-id"
    ):
        added_from_class = UserRepository.add_favorite_team(
            "user-id", " Mens ", " Soccer "
        )
        added_from_instance = UserRepository().add_favorite_team(
            "user-id", " Mens ", " Soccer "
        )
        removed_from_class = UserRepository.remove_favorite_team(
            "user-id", " Mens ", " Soccer "
        )

    expected_teams = [{"gender": "Mens", "sport": "Soccer"}]
    assert added_from_class.favorite_teams == expected_teams
    assert added_from_instance.favorite_teams == expected_teams
    assert removed_from_class.favorite_teams == expected_teams
    assert collection.find_one_and_update.call_count == 3
    for call in collection.find_one_and_update.call_args_list:
        assert call.kwargs["return_document"] == ReturnDocument.AFTER
