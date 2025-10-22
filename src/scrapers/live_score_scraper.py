import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from src.utils.constants import SIDEARM_SPORTS
from src.services.game_service import GameService
from src.services.team_service import TeamService
from src.models.game import Game

logger = logging.getLogger(__name__)


class LiveScoreScraper:
    """
    Scraper for fetching live game data from Sidearm Stats API.
    """
    
    BASE_URL = "https://sidearmstats.com/cornell/{sport}/game.json?detail=full"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_live_games(self) -> List[Dict]:
        """
        Get all currently active games across all supported sports.
        
        Returns:
            List of active game data from Sidearm API
        """
        active_games = []
        
        for sport_code, sport_info in SIDEARM_SPORTS.items():
            try:
                game_data = self._fetch_sport_data(sport_code)
                if game_data and self._is_game_active(game_data):
                    game_data['sport_code'] = sport_code
                    game_data['sport_info'] = sport_info
                    active_games.append(game_data)
                    logger.info(f"Found active {sport_info['sport']} game")
            except Exception as e:
                logger.error(f"Error fetching data for {sport_code}: {str(e)}")
                continue
        
        return active_games
    
    def _fetch_sport_data(self, sport_code: str) -> Optional[Dict]:
        """
        Fetch game data for a specific sport from Sidearm API.
        
        Args:
            sport_code: The sport code (e.g., 'msoc', 'wsoc', 'football')
            
        Returns:
            Game data dictionary or None if no active game
        """
        url = self.BASE_URL.format(sport=sport_code)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data for {sport_code}: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Invalid JSON response for {sport_code}: {str(e)}")
            return None
    
    def _is_game_active(self, game_data: Dict) -> bool:
        """
        Check if a game is currently active (started but not completed).
        
        Args:
            game_data: Game data from Sidearm API
            
        Returns:
            True if game is active, False otherwise
        """
        if not game_data or 'Game' not in game_data:
            return False
        
        game = game_data['Game']
        return (
            game.get('HasStarted', False) and 
            not game.get('IsComplete', False)
        )
    
    def get_game_plays(self, game_data: Dict) -> List[Dict]:
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
            converted_play = self._convert_play_to_our_format(play, game)
            if converted_play:
                converted_plays.append(converted_play)
        
        return converted_plays
    
    def _convert_play_to_our_format(self, play: Dict, game: Dict) -> Optional[Dict]:
        """
        Convert a Sidearm play to our box score format.
        
        Args:
            play: Play data from Sidearm API
            game: Game data from Sidearm API
            
        Returns:
            Play in our format or None if conversion fails
        """
        try:
            # Extract basic play information
            description = play.get('Description', '')
            time = play.get('Time', '')
            period = play.get('Period', 1)
            
            # Determine which team scored
            home_team = game.get('HomeTeam', {})
            visiting_team = game.get('VisitingTeam', {})
            
            # Check if it's a scoring play
            is_scoring_play = any(keyword in description.upper() for keyword in ['GOAL', 'SCORE', 'TOUCHDOWN', 'FIELD GOAL'])
            
            if not is_scoring_play:
                return None
            
            # Determine team and scores
            if 'COR' in description.upper() or 'CORNELL' in description.upper():
                team = 'COR'
                # Get current scores
                cor_score = home_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else visiting_team.get('Score', 0)
                opp_score = visiting_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else home_team.get('Score', 0)
            else:
                team = 'OPP'
                # Get current scores
                cor_score = home_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else visiting_team.get('Score', 0)
                opp_score = visiting_team.get('Score', 0) if home_team.get('Name', '').upper() == 'CORNELL' else home_team.get('Score', 0)
            
            return {
                'corScore': cor_score,
                'oppScore': opp_score,
                'team': team,
                'period': period,
                'time': time,
                'description': description,
                'scorer': None,
                'assist': None,
                'scoreBy': None
            }
            
        except Exception as e:
            logger.error(f"Error converting play: {str(e)}")
            return None
    
    def find_matching_game(self, game_data: Dict) -> Optional[Game]:
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
        opponent_team = TeamService.get_team_by_name(opponent_name)
        if not opponent_team:
            logger.warning(f"Could not find opponent team: {opponent_name}")
            return None
        
        # Get game date
        game_date = game.get('Date', '')
        if not game_date:
            return None
        
        # Try to find matching game
        sport = sport_info.get('sport', '')
        gender = sport_info.get('gender', '')
        
        # Search for games with this opponent and sport/gender
        games = GameService.get_games_by_sport_gender(sport, gender)
        
        for db_game in games:
            if (db_game.opponent_id == opponent_team.id and 
                self._dates_match(db_game.date, game_date)):
                return db_game
        
        return None
    
    def _dates_match(self, db_date: str, sidearm_date: str) -> bool:
        """
        Check if two date strings represent the same date.
        
        Args:
            db_date: Date from our database
            sidearm_date: Date from Sidearm API
            
        Returns:
            True if dates match, False otherwise
        """
        try:
            # Parse Sidearm date (format: "9/29/2025")
            sidearm_dt = datetime.strptime(sidearm_date, "%m/%d/%Y")
            
            numToMonth = {
                "1": "Jan",
                "2": "Feb",
                "3": "Mar",
                "4": "Apr",
                "5": "May",
                "6": "Jun",
                "8": "Aug",
                "9": "Sep",
                "10": "Oct",
                "11": "Nov",
                "12": "Dec"
            }
            
            year = str(sidearm_dt.year)
            month = numToMonth[str(sidearm_dt.month)]
            date = str(sidearm_dt.day)
            
            # This is simple check - might need to improve this
            if month in db_date and date in db_date and year in db_date:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error comparing dates: {str(e)}")
            return False
    
    def update_game_with_live_data(self, game: Game, game_data: Dict) -> bool:
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
            new_plays = self.get_game_plays(game_data)
            
            if not new_plays:
                return False
            
            # Get existing box score
            existing_box_score = game.box_score or []
            
            # Filter out duplicate plays
            unique_plays = self._filter_duplicate_plays(existing_box_score, new_plays)
            
            if not unique_plays:
                return False
            
            # Update box score
            updated_box_score = existing_box_score + unique_plays
            
            # Update score breakdown if needed
            updated_score_breakdown = self._update_score_breakdown(game_data, game)
            
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
    
    def _filter_duplicate_plays(self, existing_plays: List[Dict], new_plays: List[Dict]) -> List[Dict]:
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
    
    def _update_score_breakdown(self, game_data: Dict, game: Game) -> List[List[str]]:
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
        score_breakdown = []
        for i in range(len(cor_period_scores)):
            score_breakdown.append([
                str(opp_period_scores[i]) if i < len(opp_period_scores) else "0",
                str(cor_period_scores[i])
            ])
        
        return score_breakdown
