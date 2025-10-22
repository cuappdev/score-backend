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
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        # Track which clients are subscribed to which games
        self.game_subscribers: Dict[str, Set[str]] = {}  # game_id -> set of client_ids
        # Track client connections
        self.client_connections: Dict[str, Dict[str, Any]] = {}  # client_id -> connection_info
        
    def handle_connect(self, client_id: str, connection_info: Dict[str, Any] = None):
        """
        Handle a new WebSocket connection.
        
        Args:
            client_id: Unique identifier for the client
            connection_info: Additional connection metadata
        """
        self.client_connections[client_id] = connection_info or {}
        logger.info(f"Client {client_id} connected")
        
    def handle_disconnect(self, client_id: str):
        """
        Handle a WebSocket disconnection.
        
        Args:
            client_id: Unique identifier for the client
        """
        # Remove client from all game subscriptions
        for game_id, subscribers in self.game_subscribers.items():
            subscribers.discard(client_id)
            
        # Clean up empty subscription sets
        self.game_subscribers = {
            game_id: subscribers 
            for game_id, subscribers in self.game_subscribers.items() 
            if subscribers
        }
        
        # Remove client connection
        if client_id in self.client_connections:
            del self.client_connections[client_id]
            
        logger.info(f"Client {client_id} disconnected")
        
    def subscribe_to_game(self, client_id: str, game_id: str) -> bool:
        """
        Subscribe a client to live updates for a specific game.
        
        Args:
            client_id: Unique identifier for the client
            game_id: ID of the game to subscribe to
            
        Returns:
            True if subscription was successful, False otherwise
        """
        if client_id not in self.client_connections:
            logger.warning(f"Client {client_id} not found for subscription to game {game_id}")
            return False
            
        # Add client to game subscribers
        if game_id not in self.game_subscribers:
            self.game_subscribers[game_id] = set()
            
        self.game_subscribers[game_id].add(client_id)
        
        # Join the game room for targeted messaging
        join_room(f"game_{game_id}", sid=client_id)
        
        logger.info(f"Client {client_id} subscribed to game {game_id}")
        return True
        
    def unsubscribe_from_game(self, client_id: str, game_id: str) -> bool:
        """
        Unsubscribe a client from live updates for a specific game.
        
        Args:
            client_id: Unique identifier for the client
            game_id: ID of the game to unsubscribe from
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        if game_id in self.game_subscribers:
            self.game_subscribers[game_id].discard(client_id)
            
            # Clean up empty subscription sets
            if not self.game_subscribers[game_id]:
                del self.game_subscribers[game_id]
                
        # Leave the game room
        leave_room(f"game_{game_id}", sid=client_id)
        
        logger.info(f"Client {client_id} unsubscribed from game {game_id}")
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
        
    def is_client_subscribed(self, client_id: str, game_id: str) -> bool:
        """
        Check if a client is subscribed to a specific game.
        
        Args:
            client_id: Unique identifier for the client
            game_id: ID of the game
            
        Returns:
            True if client is subscribed, False otherwise
        """
        return (game_id in self.game_subscribers and 
                client_id in self.game_subscribers[game_id])
        
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """
        Get all games that a client is subscribed to.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Set of game IDs that the client is subscribed to
        """
        subscriptions = set()
        for game_id, subscribers in self.game_subscribers.items():
            if client_id in subscribers:
                subscriptions.add(game_id)
        return subscriptions


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
