import logging
import os
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

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

    @staticmethod
    def send_upcoming_game_notifications():
        """
        Batch notification sender called after each scraper run.

        Sends two types of push notifications:
          - Day-before:  game is 12–24 hours away
          - Week-before: game is 156–168 hours away (one 12-hour scraper window
                         centred on the 7-day mark)

        DB queries: 3 total (games, teams, devices) regardless of game count.
        Firebase calls: one multicast per qualifying game.
        """
        from src.database import db

        now = datetime.now(timezone.utc)

        day_start  = (now + timedelta(hours=12)).isoformat()
        day_end    = (now + timedelta(hours=24)).isoformat()
        week_start = (now + timedelta(hours=156)).isoformat()
        week_end   = (now + timedelta(hours=168)).isoformat()
        
        games = list(db["game"].find({
            "utc_date": {"$ne": None},
            "$or": [
                {"utc_date": {"$gte": day_start,  "$lte": day_end}},
                {"utc_date": {"$gte": week_start, "$lte": week_end}},
            ],
        }))

        if not games:
            return

        opponent_ids = list({g["opponent_id"] for g in games if g.get("opponent_id")})
        teams = {
            str(t["_id"]): t.get("name", "Opponent")
            for t in db["team"].find({"_id": {"$in": opponent_ids}})
        }

        devices = list(db["devices"].find({"current_fcm_token": {"$nin": [None, ""]}}))

        sport_to_tokens: dict[str, set] = {}
        for device in devices:
            token = (device.get("current_fcm_token") or "").strip()
            if not token:
                continue
            for sport in (device.get("sports") or []):
                sport_to_tokens.setdefault(sport, set()).add(token)

        for g in games:
            utc_date = g.get("utc_date")
            sport    = g.get("sport", "")
            opponent = teams.get(str(g.get("opponent_id", "")), "Opponent")

            if day_start <= utc_date <= day_end:
                title = "Game Tomorrow!"
                body  = f"Cornell {sport} vs {opponent} is tomorrow!"
            elif week_start <= utc_date <= week_end:
                title = "Game This Week!"
                body  = f"Cornell {sport} vs {opponent} is in one week!"
            else:
                continue

            tokens = list(sport_to_tokens.get(sport) or set())
            if tokens:
                logger.info(f"Sending '{title}' notification for {sport} vs {opponent} to {len(tokens)} device(s).")
                NotificationService.send_notification(tokens, title, body)

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

        response = messaging.send_each_for_multicast(message)
        failed_tokens = []
        for idx, send_response in enumerate(response.responses):
            if not send_response.success:
                token = tokens[idx]
                failed_tokens.append(token)

        if failed_tokens:
            from src.database import db
            db["devices"].update_many(
                {"current_fcm_token": {"$in": failed_tokens}},
                {"$unset": {"current_fcm_token": ""}},
            )

        return response