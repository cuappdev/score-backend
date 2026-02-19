"""
WebSocket connection manager for handling real-time game subscriptions.
"""

import logging
from typing import Dict, Set, Any, Optional
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and real-time subscriptions for live games.
    Uses SocketIO session id (request.sid) as the connection key so join_room/leave_room
    and emit(room=...) target the correct client.
    """

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        # game_id -> set of sids (SocketIO session ids)
        self.game_subscribers: Dict[str, Set[str]] = {}
        # sid -> connection_info
        self.client_connections: Dict[str, Dict[str, Any]] = {}

    def handle_connect(self, sid: str, connection_info: Dict[str, Any] = None):
        """
        Handle a new WebSocket connection.

        Args:
            sid: SocketIO session id (request.sid) for this connection
            connection_info: Optional connection metadata
        """
        self.client_connections[sid] = connection_info or {}
        logger.info(f"Client connected: {sid}")
        
    def handle_disconnect(self, sid: str):
        """
        Handle a WebSocket disconnection.

        Args:
            sid: SocketIO session id (request.sid) for the disconnecting connection
        """
        for game_id, subscribers in self.game_subscribers.items():
            subscribers.discard(sid)

        self.game_subscribers = {
            gid: subs for gid, subs in self.game_subscribers.items() if subs
        }

        if sid in self.client_connections:
            del self.client_connections[sid]

        logger.info(f"Client disconnected: {sid}")

    def subscribe_to_game(self, sid: str, game_id: str) -> bool:
        """
        Subscribe a client to live updates for a specific game.
        Joins the SocketIO room so broadcast_game_update reaches this client.

        Args:
            sid: SocketIO session id (request.sid)
            game_id: ID of the game to subscribe to

        Returns:
            True if subscription was successful, False otherwise
        """
        if sid not in self.client_connections:
            logger.warning(f"Unknown sid {sid} for subscription to game {game_id}")
            return False

        if game_id not in self.game_subscribers:
            self.game_subscribers[game_id] = set()

        self.game_subscribers[game_id].add(sid)
        join_room(f"game_{game_id}", sid=sid)

        logger.info(f"Client {sid} subscribed to game {game_id}")
        return True

    def unsubscribe_from_game(self, sid: str, game_id: str) -> bool:
        """
        Unsubscribe a client from live updates for a specific game.

        Args:
            sid: SocketIO session id (request.sid)
            game_id: ID of the game to unsubscribe from

        Returns:
            True if unsubscription was successful, False otherwise
        """
        if game_id in self.game_subscribers:
            self.game_subscribers[game_id].discard(sid)
            if not self.game_subscribers[game_id]:
                del self.game_subscribers[game_id]

        leave_room(f"game_{game_id}", sid=sid)
        logger.info(f"Client {sid} unsubscribed from game {game_id}")
        return True
        
    def broadcast_game_update(self, game_id: str, update_data: Dict[str, Any]):
        """
        Broadcast a game update to all subscribed clients.
        
        Args:
            game_id: ID of the game that was updated
            update_data: The update data to send
        """
        if game_id not in self.game_subscribers:
            logger.debug(f"No subscribers for game {game_id}")
            return
            
        subscribers = self.game_subscribers[game_id]
        if not subscribers:
            logger.debug(f"No active subscribers for game {game_id}")
            return
            
        # Prepare the update message
        message = {
            'type': 'game_update',
            'gameId': game_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': update_data
        }
        
        # Broadcast to all subscribers of this game
        self.socketio.emit('game_update', message, room=f"game_{game_id}")
        
        logger.info(f"Broadcasted game update for {game_id} to {len(subscribers)} subscribers")
        
    def get_game_subscriber_count(self, game_id: str) -> int:
        """
        Get the number of subscribers for a specific game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Number of active subscribers
        """
        return len(self.game_subscribers.get(game_id, set()))
        
    def get_all_subscribers(self) -> Dict[str, int]:
        """
        Get subscriber counts for all games.
        
        Returns:
            Dictionary mapping game_id to subscriber count
        """
        return {
            game_id: len(subscribers) 
            for game_id, subscribers in self.game_subscribers.items()
        }
        
    def is_client_subscribed(self, sid: str, game_id: str) -> bool:
        """Check if the connection (sid) is subscribed to the game."""
        return (
            game_id in self.game_subscribers
            and sid in self.game_subscribers[game_id]
        )

    def get_client_subscriptions(self, sid: str) -> Set[str]:
        """Return set of game IDs the connection (sid) is subscribed to."""
        return {
            gid for gid, subscribers in self.game_subscribers.items()
            if sid in subscribers
        }


# Global WebSocket manager instance
websocket_manager: Optional[WebSocketManager] = None


def init_websocket_manager(socketio: SocketIO):
    """
    Initialize the global WebSocket manager.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    logger.info("WebSocket manager initialized")


def get_websocket_manager() -> WebSocketManager:
    """
    Get the global WebSocket manager instance.
    
    Returns:
        WebSocketManager instance
        
    Raises:
        RuntimeError: If WebSocket manager is not initialized
    """
    if websocket_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return websocket_manager