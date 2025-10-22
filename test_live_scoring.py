#!/usr/bin/env python3
"""
Test script for the live scoring system.

This script demonstrates how to use the live scoring functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.live_game_service import live_game_service
from src.scrapers.live_score_scraper import LiveScoreScraper
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_live_scraper():
    """Test the live score scraper functionality."""
    logger.info("Testing Live Score Scraper...")
    
    scraper = LiveScoreScraper()
    
    # Test fetching live games
    live_games = scraper.get_live_games()
    logger.info(f"Found {len(live_games)} active games")
    
    for game_data in live_games:
        sport_code = game_data.get('sport_code', 'unknown')
        sport_info = game_data.get('sport_info', {})
        logger.info(f"Active {sport_info.get('sport', 'Unknown')} game found")
        
        # Test finding matching game
        matching_game = scraper.find_matching_game(game_data)
        if matching_game:
            logger.info(f"Found matching game: {matching_game.id}")
            
            # Test getting plays
            plays = scraper.get_game_plays(game_data)
            logger.info(f"Found {len(plays)} plays")
            
            # Test updating game
            was_updated = scraper.update_game_with_live_data(matching_game, game_data)
            logger.info(f"Game update successful: {was_updated}")
        else:
            logger.warning("No matching game found in database")


def test_live_game_service():
    """Test the live game service functionality."""
    logger.info("Testing Live Game Service...")
    
    # Start the service
    live_game_service.start_polling()
    logger.info("Live game service started")
    
    # Wait a bit for polling to occur
    time.sleep(5)
    
    # Get active games
    active_games = live_game_service.get_active_games()
    logger.info(f"Active games: {len(active_games)}")
    
    for game in active_games:
        logger.info(f"Active game: {game.id} - {game.sport} {game.gender}")
    
    # Test subscription
    if active_games:
        game_id = active_games[0].id
        subscriber_id = "test_subscriber"
        
        success = live_game_service.subscribe_to_game(game_id, subscriber_id)
        logger.info(f"Subscription successful: {success}")
        
        subscriber_count = live_game_service.get_game_subscriber_count(game_id)
        logger.info(f"Subscriber count: {subscriber_count}")
        
        # Test unsubscription
        success = live_game_service.unsubscribe_from_game(game_id, subscriber_id)
        logger.info(f"Unsubscription successful: {success}")
    
    # Stop the service
    live_game_service.stop_polling()
    logger.info("Live game service stopped")


def main():
    """Main test function."""
    logger.info("Starting live scoring system tests...")
    
    try:
        # Test the scraper
        test_live_scraper()
        
        # Test the service
        test_live_game_service()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
