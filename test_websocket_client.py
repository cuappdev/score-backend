#!/usr/bin/env python3
"""
WebSocket test client for live game subscriptions.

This script demonstrates how to connect to the WebSocket server and subscribe to live game updates.
"""

import socketio
import time
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiveGameWebSocketClient:
    """
    WebSocket client for testing live game subscriptions.
    """
    
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.sio = socketio.Client()
        self.setup_event_handlers()
        self.connected = False
        
    def setup_event_handlers(self):
        """Setup WebSocket event handlers."""
        
        @self.sio.event
        def connect():
            """Handle connection."""
            logger.info("Connected to WebSocket server")
            self.connected = True
            
        @self.sio.event
        def disconnect():
            """Handle disconnection."""
            logger.info("Disconnected from WebSocket server")
            self.connected = False
            
        @self.sio.event
        def connected(data):
            """Handle connection confirmation."""
            logger.info(f"Connection confirmed: {data}")
            
        @self.sio.event
        def game_update(data):
            """Handle game update."""
            logger.info(f"Game update received: {json.dumps(data, indent=2)}")
            
        @self.sio.event
        def subscription_success(data):
            """Handle successful subscription."""
            logger.info(f"Subscription successful: {data}")
            
        @self.sio.event
        def unsubscription_success(data):
            """Handle successful unsubscription."""
            logger.info(f"Unsubscription successful: {data}")
            
        @self.sio.event
        def error(data):
            """Handle errors."""
            logger.error(f"Error: {data}")
            
        @self.sio.event
        def subscriptions(data):
            """Handle subscriptions list."""
            logger.info(f"Current subscriptions: {data}")
            
        @self.sio.event
        def game_info(data):
            """Handle game information."""
            logger.info(f"Game info: {json.dumps(data, indent=2)}")
            
        @self.sio.event
        def pong(data):
            """Handle pong response."""
            logger.info(f"Pong received: {data}")
    
    def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.sio.connect(self.server_url)
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.connected:
            self.sio.disconnect()
    
    def subscribe_to_game(self, game_id: str):
        """Subscribe to live updates for a specific game."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        self.sio.emit('subscribe_game', {'gameId': game_id})
        return True
    
    def unsubscribe_from_game(self, game_id: str):
        """Unsubscribe from live updates for a specific game."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        self.sio.emit('unsubscribe_game', {'gameId': game_id})
        return True
    
    def get_subscriptions(self):
        """Get current subscriptions."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        self.sio.emit('get_subscriptions')
        return True
    
    def get_game_info(self, game_id: str):
        """Get information about a specific game."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        self.sio.emit('get_game_info', {'gameId': game_id})
        return True
    
    def ping(self):
        """Send ping to server."""
        if not self.connected:
            logger.error("Not connected to server")
            return False
            
        self.sio.emit('ping')
        return True
    
    def wait_for_updates(self, duration: int = 60):
        """Wait for updates for a specified duration."""
        logger.info(f"Waiting for updates for {duration} seconds...")
        time.sleep(duration)


def main():
    """Main test function."""
    logger.info("Starting WebSocket client test...")
    
    # Create client
    client = LiveGameWebSocketClient()
    
    try:
        # Connect to server
        if not client.connect():
            logger.error("Failed to connect to server")
            return
        
        # Wait a moment for connection to establish
        time.sleep(1)
        
        # Test ping
        logger.info("Testing ping...")
        client.ping()
        time.sleep(1)
        
        # Get current subscriptions
        logger.info("Getting current subscriptions...")
        client.get_subscriptions()
        time.sleep(1)
        
        # Subscribe to a test game (replace with actual game ID)
        test_game_id = "68ddf5db6085081a77a6120a"  # Replace with actual game ID
        logger.info(f"Subscribing to game {test_game_id}...")
        client.subscribe_to_game(test_game_id)
        time.sleep(1)
        
        # Get game info
        logger.info(f"Getting info for game {test_game_id}...")
        client.get_game_info(test_game_id)
        time.sleep(1)
        
        # Get subscriptions again
        logger.info("Getting subscriptions after subscription...")
        client.get_subscriptions()
        time.sleep(1)
        
        # Wait for updates
        logger.info("Waiting for live updates...")
        client.wait_for_updates(30)  # Wait 30 seconds for updates
        
        # Unsubscribe
        logger.info(f"Unsubscribing from game {test_game_id}...")
        client.unsubscribe_from_game(test_game_id)
        time.sleep(1)
        
        # Get final subscriptions
        logger.info("Getting final subscriptions...")
        client.get_subscriptions()
        time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        # Disconnect
        client.disconnect()
        logger.info("Test completed")


if __name__ == "__main__":
    main()
