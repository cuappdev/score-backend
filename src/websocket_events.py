"""
WebSocket event handlers for live game subscriptions.
Uses request.sid (SocketIO session id) as the connection identifier so room joins
and broadcasts target the correct client.
"""

import logging
from flask import request
from flask_socketio import emit, disconnect
from src.websocket_manager import get_websocket_manager
from src.services.game_service import GameService

logger = logging.getLogger(__name__)


def register_websocket_events(socketio):
    """
    Register WebSocket event handlers with the SocketIO instance.
    
    Args:
        socketio: Flask-SocketIO instance
    """

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection. Use request.sid as the connection id."""
        sid = request.sid
        logger.info(f"Client connected: {sid}")

        websocket_manager = get_websocket_manager()
        websocket_manager.handle_connect(sid)

        emit('connected', {'clientId': sid, 'status': 'success'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection. request.sid is still available here."""
        sid = request.sid
        logger.info(f"Client disconnected: {sid}")

        websocket_manager = get_websocket_manager()
        websocket_manager.handle_disconnect(sid)
            
    @socketio.on('subscribe_game')
    def handle_subscribe_game(data):
        """
        Handle game subscription request.
        
        Expected data format:
        {
            "gameId": "68ddf5db6085081a77a6120a"
        }
        """
        sid = request.sid
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return

        game = GameService.get_game_by_id(game_id)
        if not game:
            emit('error', {'message': f'Game {game_id} not found'})
            return

        websocket_manager = get_websocket_manager()
        success = websocket_manager.subscribe_to_game(sid, game_id)

        if success:
            emit('subscription_success', {
                'gameId': game_id,
                'message': f'Successfully subscribed to game {game_id}'
            })
            logger.info(f"Client {sid} subscribed to game {game_id}")
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
        sid = request.sid
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return

        websocket_manager = get_websocket_manager()
        success = websocket_manager.unsubscribe_from_game(sid, game_id)

        if success:
            emit('unsubscription_success', {
                'gameId': game_id,
                'message': f'Successfully unsubscribed from game {game_id}'
            })
            logger.info(f"Client {sid} unsubscribed from game {game_id}")
        else:
            emit('error', {'message': 'Failed to unsubscribe from game'})
            
    @socketio.on('get_subscriptions')
    def handle_get_subscriptions():
        """Handle request for current subscriptions."""
        sid = request.sid
        websocket_manager = get_websocket_manager()
        subscriptions = websocket_manager.get_client_subscriptions(sid)

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
        game_id = data.get('gameId')
        if not game_id:
            emit('error', {'message': 'Game ID is required'})
            return

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