import os
import firebase_admin
from firebase_admin import credentials, messaging

class NotificationService:

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',))
    service_account_path = os.path.join(base_dir, 'firebase_serviceAccountKey.json')

    if not os.path.exists(service_account_path):
        raise FileNotFoundError(
            f"Firebase service account key not found at {service_account_path}. "
            "Please ensure it exists in the project root folder and is excluded from version control."
        )

    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

    def send_notification (tokens: list, title: str, body: str):
        """
        Sends a notification to multiple device tokens.
        Returns a response object with success_count and failure_count.
        """
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens,
        )

        # create a token creation graphql mutation that accepts an fcm token and possibly a user id and timestamp
        # occasionally remove tokens that are older than 30 days using a script that runs every day at midnight
        # in the database associate the token with game ids/sports that the user has favorited
        # in send_notfiication method, delete the token if it fails
        # in the games scraping script, send notifications to the user for games that are upcoming and they have favorited by querying the tokens and using $in to check tokens that have the game id/sport
        # might have to create device_id table that stores device id with current fcm token
        
        # devices table that store device id, current fcm token, and preferences (game ids/sports that the user has favorited)
        # anytime user refreshes token, update the device table with the new token and add token to token table with timestamp
        # anytime token is invalid or its past its timestamp, delete the token
        # in the games scraping script, send notifications to the user for games that are upcoming and they have favorited by querying the tokens and using $in to check tokens that have the game id/sport
        return messaging.send_each_for_multicast(message)