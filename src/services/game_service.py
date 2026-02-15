from src.repositories.game_repository import GameRepository
from src.models.game import Game
from src.services.team_service import TeamService
from src.utils.helpers import is_tournament_placeholder_team, sidearm_dates_match
from typing import Dict, List, Optional, Tuple
from pymongo.errors import DuplicateKeyError
import requests
from bs4 import BeautifulSoup
from src.utils.constants import SIDEARM_SPORTS
import logging
from src.utils.helpers import convert_play_to_our_format

logger = logging.getLogger(__name__)

class GameService:
    @staticmethod
    def get_all_games(limit=100, offset=0):
        """
        Retrieves all games with pagination.

        Args:
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip

        Returns:
            list: A list of game documents
        """
        return GameRepository.find_all(limit=limit, offset=offset)

    @staticmethod
    def get_game_by_id(game_id):
        """
        Retrieve a game by its ID.
        """
        return GameRepository.find_by_id(game_id)

    @staticmethod
    def create_game(data):
        """
        Create a new game.
        """
        opponent_id = data.get("opponent_id")
        if not TeamService.get_team_by_id(opponent_id):
            raise ValueError(f"Opponent team with id {opponent_id} does not exist.")

        game = Game(**data)
        try:
            GameRepository.insert(game)
            return game
        except DuplicateKeyError:
            return None

    @staticmethod
    def delete_game(game_id):
        """
        Delete a game by its ID.
        """
        GameRepository.delete_by_id(game_id)

    @staticmethod
    def update_game(game_id, data):
        """
        Update a game by its ID.
        """
        GameRepository.update_by_id(game_id, data)

    @staticmethod
    def get_game_by_data(city, date, gender, location, opponent_id, sport, state, time):
        """
        Retrieve a game by its data.
        """
        return GameRepository.find_by_data(
            city, date, gender, location, opponent_id, sport, state, time
        )

    @staticmethod
    def get_game_by_key_fields(city, date, gender, location, opponent_id, sport, state):
        """
        Retrieve a game by its essential fields, ignoring time
        """
        return GameRepository.find_by_key_fields(
            city, date, gender, location, opponent_id, sport, state
        )

    @staticmethod
    def get_game_by_tournament_key_fields(city, date, gender, location, sport, state):
        """
        Retrieve a tournament game by location and date (excluding opponent_id).
        This is used when we need to find a tournament game that might have a placeholder team.
        """
        return GameRepository.find_by_tournament_key_fields(
            city, date, gender, location, sport, state
        )

    @staticmethod
    def get_games_by_sport(sport):
        """
        Retrieves all game by its sport.
        """
        return GameRepository.find_by_sport(sport)

    @staticmethod
    def get_games_by_gender(gender):
        """
        Retrieves all games by its gender.
        """
        return GameRepository.find_by_gender(gender)

    @staticmethod
    def get_games_by_sport_gender(sport, gender):
        """
        Retrieves all game by its sport and gender.
        """
        return GameRepository.find_by_sport_gender(sport, gender)
    
    @staticmethod
    def get_games_by_date(startDate, endDate):
        """
        Retrieves all games between these two dates.
        """
        return GameRepository.find_by_date(startDate, endDate)

    @staticmethod
    def get_tournament_games_by_sport_gender(sport, gender, after_date=None):
        """
        Find tournament games (with placeholder team names) for a specific sport and gender.
        Optionally filter by games after a specific date.
        """
        games = GameRepository.find_games_by_sport_gender_after_date(sport, gender, after_date)
        tournament_games = []
        
        for game in games:
            team = TeamService.get_team_by_id(game.opponent_id)
            if team and is_tournament_placeholder_team(team.name):
                tournament_games.append(game)
        
        return tournament_games

    @staticmethod
    def delete_tournament_games_by_sport_gender(sport, gender, after_date=None):
        """
        Delete tournament games (with placeholder team names) for a specific sport and gender.
        Optionally filter by games after a specific date.
        """
        games = GameRepository.find_games_by_sport_gender_after_date(sport, gender, after_date)
        tournament_game_ids = []
        
        for game in games:
            team = TeamService.get_team_by_id(game.opponent_id)
            if team and is_tournament_placeholder_team(team.name):
                tournament_game_ids.append(game.id)
        
        if tournament_game_ids:
            return GameRepository.delete_games_by_ids(tournament_game_ids)
        return 0

    @staticmethod
    def handle_tournament_loss(sport, gender, loss_date):
        """
        Handle when a Cornell team loses in a tournament by deleting future tournament games.
        
        Args:
            sport (str): The sport of the team that lost
            gender (str): The gender of the team that lost  
            loss_date (datetime): The date when the team lost
        """
        deleted_count = GameService.delete_tournament_games_by_sport_gender(sport, gender, loss_date)
        return deleted_count
    
    @staticmethod
    def update_live_game(game):
        """
        Update a live game with live game data from cornellbigred.com.
        """
        # update the game with the new score, box score, and score breakdown
        # GameRepository.update_by_id(game.id, game)
        if game["media"]["stats"] is not None and game["media"]["stats"]["url"] != None:
            stats_url = game["media"]["stats"]["url"]
            # handle sidearmstats for now
            if not stats_url.startswith("https://cornellbigred.com/sidearmstats/") and not stats_url.startswith("http://www.sidearmstats.com"):
                return

            sport = stats_url.split("/")[4]
            params = {
                "detail": "full"
            }

            # print("sport: ", sport)

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": stats_url,
            }

            url = f"https://sidearmstats.com/cornell/{sport}/game.json"
            r = requests.get(url, params=params, headers=headers, timeout=10)
            game_data = r.json()
            game_data["sport_code"] = sport
            game_data["sport_info"] = SIDEARM_SPORTS[sport]

            matching_game = GameService.find_matching_game(game_data)
            if matching_game:
                game_id = matching_game.id
                print("matching game id: ",game_id)
                was_updated = GameService.update_game_with_new_data(matching_game, game_data)
                # notify all subscribers
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
                    try:
                        from src.websocket_manager import get_websocket_manager
                        websocket_manager = get_websocket_manager()
                        subscriber_count = websocket_manager.get_game_subscriber_count(game_id)
                        logger.info(f"Notifying {subscriber_count} subscribers of game {game_id} update")
                        
                        # Prepare update data
                        update_data = {
                            'gameId': game_id,
                            'isLive': True,
                            'lastUpdated': datetime.now(timezone.utc).isoformat(),
                            'boxScore': matching_game.box_score,
                            'scoreBreakdown': matching_game.score_breakdown,
                            'result': matching_game.result
                        }
                        
                        # Broadcast to WebSocket subscribers
                        websocket_manager.broadcast_game_update(game_id, update_data)
                        
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket notification for game {game_id}: {str(e)}")
            else:
                print("create new game in db")
    
    def find_matching_game(game_data: Dict) -> Optional[Game]:
        """
        Find the matching game in our database based on Sidearm data.
        
        Args:
            game_data: Game data from Sidearm API
            
        Returns:
            Matching Game object or None
        """
        if not game_data or 'Game' not in game_data:
            return None
        
        game = game_data['Game']
        sport_info = game_data.get('sport_info', {})
        
        # Extract game information
        home_team = game.get('HomeTeam', {})
        visiting_team = game.get('VisitingTeam', {})
        
        # Determine opponent
        if home_team.get('Name', '').upper() == 'CORNELL':
            opponent_name = visiting_team.get('Name', '')
        else:
            opponent_name = home_team.get('Name', '')
        
        # Find opponent team in our database
        print("opponent_name: ", opponent_name)
        opponent_team = TeamService.get_teams_by_name_containing(opponent_name)
        if not opponent_team:
            logger.warning(f"Could not find opponent team: {opponent_name}")
            return None
        
        
        # Get game date
        game_date = game.get('Date', '')
        if not game_date:
            return None
        
        # Try to find matching game
        sport, gender = SIDEARM_SPORTS[game.get('GlobalSportShortname', '')].values()
        
        # Search for games with this opponent and sport/gender
        games = GameService.get_games_by_sport_gender(sport, gender)
        
        for db_game in games:
            for opp_team in opponent_team:
                if (db_game.opponent_id == opp_team.id and 
                    sidearm_dates_match(db_game.date, game_date)):
                    return db_game
        return None
    
    def filter_duplicate_plays(existing_plays: List[Dict], new_plays: List[Dict]) -> List[Dict]:
        """
        Filter out plays that already exist in the game.
        
        Args:
            existing_plays: List of existing plays
            new_plays: List of new plays to check
            
        Returns:
            List of unique new plays
        """
        unique_plays = []
        
        for new_play in new_plays:
            is_duplicate = False
            
            for existing_play in existing_plays:
                if (new_play.get('description') == existing_play.get('description') and
                    new_play.get('time') == existing_play.get('time')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_plays.append(new_play)
        
        return unique_plays
    
    def update_score_breakdown(game_data: Dict, game: Game) -> List[List[str]]:
        """
        Update score breakdown based on live data.
        
        Args:
            game_data: Live data from Sidearm API
            game: Game object
            
        Returns:
            Updated score breakdown
        """
        if not game_data or 'Game' not in game_data:
            return game.score_breakdown or []
        
        game_info = game_data['Game']
        home_team = game_info.get('HomeTeam', {})
        visiting_team = game_info.get('VisitingTeam', {})
        
        # Determine which team is Cornell
        if home_team.get('Name', '').upper() == 'CORNELL':
            cor_period_scores = home_team.get('PeriodScores', [])
            opp_period_scores = visiting_team.get('PeriodScores', [])
        else:
            cor_period_scores = visiting_team.get('PeriodScores', [])
            opp_period_scores = home_team.get('PeriodScores', [])
        
        # Convert to our format
        score_breakdown = [[], []]
        for i in range(len(cor_period_scores)):
            score_breakdown[0].append(str(cor_period_scores[i]))
            score_breakdown[1].append(str(opp_period_scores[i]) if i < len(opp_period_scores) else "0")
        
        return score_breakdown
    
    def get_game_plays(game_data: Dict) -> List[Dict]:
        """
        Extract plays from game data and convert to our format.
        
        Args:
            game_data: Game data from Sidearm API
            
        Returns:
            List of plays in our format
        """
        if not game_data or 'Game' not in game_data:
            return []
        
        game = game_data['Game']
        plays = game.get('LastPlays', [])
        
        converted_plays = []
        for play in plays:
            converted_play = convert_play_to_our_format(play, game)
            if converted_play:
                converted_plays.append(converted_play)
        
        return converted_plays

    def update_game_with_new_data(game: Game, game_data: Dict) -> bool:
        """
        Update a game with live score data.
        
        Args:
            game: Game object to update
            game_data: Live data from Sidearm API
            
        Returns:
            True if game was updated, False otherwise
        """
        try:
            # Get new plays
            new_plays = GameService.get_game_plays(game_data)
            
            if not new_plays:
                return False
            
            # Get existing box score
            existing_box_score = game.box_score or []
            
            # Filter out duplicate plays
            unique_plays = GameService.filter_duplicate_plays(existing_box_score, new_plays)
            
            if not unique_plays:
                return False
            
            # Update box score
            updated_box_score = existing_box_score + unique_plays
            
            # Update score breakdown if needed
            updated_score_breakdown = GameService.update_score_breakdown(game_data, game)

            print("updated box score: ",updated_box_score)
            print("updated_score_breakdown: ",updated_score_breakdown)
            
            # Update the game
            update_data = {
                'box_score': updated_box_score,
                'score_breakdown': updated_score_breakdown
            }
            
            GameService.update_game(game.id, update_data)
            logger.info(f"Updated game {game.id} with {len(unique_plays)} new plays")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating game {game.id}: {str(e)}")
            return False