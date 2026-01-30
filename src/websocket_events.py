"""
WebSocket event handlers for live game subscriptions.
"""

import logging
from flask_socketio import emit, disconnect
from src.websocket_manager import get_websocket_manager
from src.services.game_service import GameService
import uuid

logger = logging.getLogger(__name__)


def register_websocket_events(socketio):
    """
    Register WebSocket event handlers with the SocketIO instance.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        client_id = str(uuid.uuid4())
        logger.info(f"Client connected: {client_id}")
        
        # Store client ID in session
        from flask import session
        session['client_id'] = client_id
        
        # Register with WebSocket manager
        websocket_manager = get_websocket_manager()
        websocket_manager.handle_connect(client_id)
        
        emit('connected', {'clientId': client_id, 'status': 'success'})
        
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        from flask import session
        client_id = session.get('client_id')
        
        if client_id:
            logger.info(f"Client disconnected: {client_id}")
            
            # Unregister from WebSocket manager
            websocket_manager = get_websocket_manager()
            websocket_manager.handle_disconnect(client_id)
        else:
            logger.warning("Client disconnected without client_id")
            
    @socketio.on('subscribe_game')
    def handle_subscribe_game(data):
        """
        Handle game subscription request.
        
        Expected data format:
        {
            "gameId": "68ddf5db6085081a77a6120a"
        }
        """
        from flask import session
        client_id = session.get('client_id')
        
        if not client_id:
            emit('error', {'message': 'Client not authenticated'})
            return
            
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return
            
        # Verify game exists
        game = GameService.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': f'Game {game_id} not found'})
            return
            
        # Subscribe to game updates
        websocket_manager = get_websocket_manager()
        success = websocket_manager.subscribe_to_game(client_id, game_id)
        
        if success:
            emit('subscription_success', {
                'gameId': game_id,
                'message': f'Successfully subscribed to game {game_id}'
            })
            logger.info(f"Client {client_id} subscribed to game {game_id}")
        else:
            emit('error', {'message': 'Failed to subscribe to game'})
            
    @socketio.on('unsubscribe_game')
    def handle_unsubscribe_game(data):
        """
        Handle game unsubscription request.
        
        Expected data format:
        {
            "gameId": "68ddf5db6085081a77a6120a"
        }
        """
        from flask import session
        client_id = session.get('client_id')
        
        if not client_id:
            emit('error', {'message': 'Client not authenticated'})
            return
            
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return
            
        # Unsubscribe from game updates
        websocket_manager = get_websocket_manager()
        success = websocket_manager.unsubscribe_from_game(client_id, game_id)
        
        if success:
            emit('unsubscription_success', {
                'gameId': game_id,
                'message': f'Successfully unsubscribed from game {game_id}'
            })
            logger.info(f"Client {client_id} unsubscribed from game {game_id}")
        else:
            emit('error', {'message': 'Failed to unsubscribe from game'})
            
    @socketio.on('get_subscriptions')
    def handle_get_subscriptions():
        """Handle request for current subscriptions."""
        from flask import session
        client_id = session.get('client_id')
        
        if not client_id:
            emit('error', {'message': 'Client not authenticated'})
            return
            
        websocket_manager = get_websocket_manager()
        subscriptions = websocket_manager.get_client_subscriptions(client_id)
        
        emit('subscriptions', {
            'subscriptions': list(subscriptions),
            'count': len(subscriptions)
        })
        
    @socketio.on('get_game_info')
    def handle_get_game_info(data):
        """
        Handle request for game information.
        
        Expected data format:
        {
            "gameId": "68ddf5db6085081a77a6120a"
        }
        """
        from flask import session
        client_id = session.get('client_id')
        
        if not client_id:
            emit('error', {'message': 'Client not authenticated'})
            return
            
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return
            
        # Get game information
        game = GameService.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': f'Game {game_id} not found'})
            return
            
        # Convert game to dictionary format
        game_data = {
            'id': game.id,
            'sport': game.sport,
            'gender': game.gender,
            'date': game.date,
            'time': game.time,
            'city': game.city,
            'state': game.state,
            'location': game.location,
            'result': game.result,
            'isLive': game.is_live,
            'lastUpdated': game.last_updated,
            'boxScore': game.box_score,
            'scoreBreakdown': game.score_breakdown
        }
        
        emit('game_info', {
            'gameId': game_id,
            'game': game_data
        })
        
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection health check."""
        emit('pong', {'timestamp': 'now'})
        
    @socketio.on_error_default
    def default_error_handler(e):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {str(e)}")
        emit('error', {'message': 'An error occurred'})