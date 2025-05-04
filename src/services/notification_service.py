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
        return messaging.send_each_for_multicast(message)

            