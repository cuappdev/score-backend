import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from src.scrapers.live_score_scraper import LiveScoreScraper
from src.models.game import Game
from src.services.game_service import GameService
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class LiveGameService:
    """
    Service to manage live game updates and subscriptions.
    """
    
    def __init__(self):
        self.scraper = LiveScoreScraper()
        self.active_games: Dict[str, Game] = {}  # game_id -> Game
        self.subscribers: Dict[str, Set[str]] = {}  # game_id -> set of subscriber_ids
        self.is_running = False
        self.polling_thread = None
        self.polling_interval = 30  # seconds
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def start_polling(self):
        """
        Start the background polling for live games.
        """
        if self.is_running:
            logger.warning("Live game polling is already running")
            return
        
        self.is_running = True
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
        logger.info("Started live game polling")
    
    def stop_polling(self):
        """
        Stop the background polling for live games.
        """
        self.is_running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=5)
        logger.info("Stopped live game polling")
    
    def _polling_loop(self):
        """
        Main polling loop that runs in a separate thread.
        """
        while self.is_running:
            try:
                self._update_active_games()
                time.sleep(self.polling_interval)
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}")
                time.sleep(self.polling_interval)
    
    def _update_active_games(self):
        """
        Update all active games with latest data.
        """
        try:
            # Get all currently active games from Sidearm
            live_games = self.scraper.get_live_games()
            
            # Track which games are still active
            currently_active_game_ids = set()
            
            for live_game_data in live_games:
                # Find matching game in our database
                matching_game = self.scraper.find_matching_game(live_game_data)
                
                if matching_game:
                    game_id = matching_game.id
                    currently_active_game_ids.add(game_id)
                    
                    # Update the game with live data
                    was_updated = self.scraper.update_game_with_live_data(matching_game, live_game_data)
                    
                    if was_updated:
                        # Update live status and timestamp
                        from datetime import datetime, timezone
                        update_data = {
                            'is_live': True,
                            'last_updated': datetime.now(timezone.utc).isoformat()
                        }
                        GameService.update_game(game_id, update_data)
                        
                        # Refresh the game object
                        matching_game = GameService.get_game_by_id(game_id)
                        
                        # Notify subscribers
                        self._notify_subscribers(game_id, matching_game)
                    
                    # Update our active games cache
                    self.active_games[game_id] = matching_game
                else:
                    logger.warning(f"Could not find matching game for live data: {live_game_data.get('sport_code', 'unknown')}")
            
            # Remove games that are no longer active
            inactive_game_ids = set(self.active_games.keys()) - currently_active_game_ids
            for game_id in inactive_game_ids:
                self._remove_active_game(game_id)
                
        except Exception as e:
            logger.error(f"Error updating active games: {str(e)}")
    
    def _notify_subscribers(self, game_id: str, game: Game):
        """
        Notify all subscribers of a game update.
        
        Args:
            game_id: ID of the game that was updated
            game: Updated game object
        """
        if game_id in self.subscribers:
            subscriber_count = len(self.subscribers[game_id])
            logger.info(f"Notifying {subscriber_count} subscribers of game {game_id} update")
          
            # Send WebSocket notification
            try:
                from src.websocket_manager import get_websocket_manager
                websocket_manager = get_websocket_manager()
                
                # Prepare update data
                update_data = {
                'gameId': game_id,
                'isLive': game.is_live,
                'lastUpdated': game.last_updated,
                'boxScore': game.box_score,
                'scoreBreakdown': game.score_breakdown,
                'result': game.result
                }
                
                # Broadcast to WebSocket subscribers
                websocket_manager.broadcast_game_update(game_id, update_data)
                
            except Exception as e:
                logger.error(f"Failed to send WebSocket notification for game {game_id}: {str(e)}")
    
    def _remove_active_game(self, game_id: str):
        """
        Remove a game from active games and clean up subscribers.
        
        Args:
            game_id: ID of the game to remove
        """
        if game_id in self.active_games:
            from datetime import datetime, timezone
            update_data = {
                'is_live': False,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            GameService.update_game(game_id, update_data)
            
            del self.active_games[game_id]
            logger.info(f"Removed game {game_id} from active games")
        
        if game_id in self.subscribers:
            del self.subscribers[game_id]
            logger.info(f"Cleaned up subscribers for game {game_id}")
    
    def subscribe_to_game(self, game_id: str, subscriber_id: str) -> bool:
        """
        Subscribe to live updates for a specific game.
        
        Args:
            game_id: ID of the game to subscribe to
            subscriber_id: Unique identifier for the subscriber
            
        Returns:
            True if subscription was successful, False otherwise
        """
        # Check if game exists
        game = GameService.get_game_by_id(game_id)
        if not game:
            logger.warning(f"Game {game_id} not found for subscription")
            return False
        
        # Add subscriber
        if game_id not in self.subscribers:
            self.subscribers[game_id] = set()
        
        self.subscribers[game_id].add(subscriber_id)
        logger.info(f"Subscribed {subscriber_id} to game {game_id}")
        
        return True
    
    def unsubscribe_from_game(self, game_id: str, subscriber_id: str) -> bool:
        """
        Unsubscribe from live updates for a specific game.
        
        Args:
            game_id: ID of the game to unsubscribe from
            subscriber_id: Unique identifier for the subscriber
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        if game_id in self.subscribers:
            self.subscribers[game_id].discard(subscriber_id)
            
            # Clean up empty subscriber sets
            if not self.subscribers[game_id]:
                del self.subscribers[game_id]
            
            logger.info(f"Unsubscribed {subscriber_id} from game {game_id}")
            return True
        
        return False
    
    def get_active_games(self) -> List[Game]:
        """
        Get all currently active games.
        
        Returns:
            List of active Game objects
        """
        return list(self.active_games.values())
    
    def is_game_active(self, game_id: str) -> bool:
        """
        Check if a game is currently active.
        
        Args:
            game_id: ID of the game to check
            
        Returns:
            True if game is active, False otherwise
        """
        return game_id in self.active_games
    
    def get_game_subscriber_count(self, game_id: str) -> int:
        """
        Get the number of subscribers for a specific game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Number of subscribers
        """
        return len(self.subscribers.get(game_id, set()))
    
    def force_update_game(self, game_id: str) -> bool:
        """
        Force an immediate update for a specific game.
        
        Args:
            game_id: ID of the game to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get the game
            game = GameService.get_game_by_id(game_id)
            if not game:
                return False
            
            # Find matching live data
            sport_info = self._get_sport_info_for_game(game)
            if not sport_info:
                return False
            
            sport_code = sport_info['sport_code']
            live_game_data = self.scraper._fetch_sport_data(sport_code)
            
            if live_game_data and self.scraper._is_game_active(live_game_data):
                live_game_data['sport_code'] = sport_code
                live_game_data['sport_info'] = sport_info
                
                # Update the game
                was_updated = self.scraper.update_game_with_live_data(game, live_game_data)
                
                if was_updated:
                    self._notify_subscribers(game_id, game)
                
                return was_updated
            
            return False
            
        except Exception as e:
            logger.error(f"Error force updating game {game_id}: {str(e)}")
            return False
    
    def _get_sport_info_for_game(self, game: Game) -> Optional[Dict]:
        """
        Get sport information for a game to determine the Sidearm sport code.
        
        Args:
            game: Game object
            
        Returns:
            Sport info dictionary with sport_code and sport_info
        """
        from src.utils.constants import SIDEARM_SPORTS
        
        # Find matching sport code
        for sport_code, sport_info in SIDEARM_SPORTS.items():
            if (sport_info.get('sport', '').lower() == game.sport.lower() and
                sport_info.get('gender', '').lower() == game.gender.lower()):
                return {
                    'sport_code': sport_code,
                    'sport_info': sport_info
                }
        
        return None

# Global instance
live_game_service = LiveGameService()
