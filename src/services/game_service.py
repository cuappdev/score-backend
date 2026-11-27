from src.repositories.game_repository import GameRepository
from src.models.game import Game
from src.services.team_service import TeamService
from src.utils.helpers import (
    build_sidearm_game_json_url,
    get_with_retries,
    is_tournament_placeholder_team,
    parse_sidearm_stats_url,
    is_game_active,
    sidearm_dates_match,
)
from typing import Dict, List, Optional, Tuple
from pymongo.errors import DuplicateKeyError
from bs4 import BeautifulSoup
from src.utils.constants import HTTP_REQUEST_HEADERS, SIDEARM_SPORTS
import logging
from datetime import datetime, timezone
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
    def get_games_by_location(onCampus):
        """
        Retrieves all games by their location.
        """
        return GameRepository.find_by_location(onCampus)

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
        stats = (game.get("media") or {}).get("stats") or {}
        stats_url = stats.get("url")
        if stats_url:
            if "sidearmstats" not in stats_url:
                return

            # The event's global_sport_shortname is the same code sidearmstats uses
            # in its paths, and is more reliable than parsing it out of the URL.
            _, url_sport = parse_sidearm_stats_url(stats_url)
            sport = (game.get("sport") or {}).get("global_sport_shortname") or url_sport

            sport_info = SIDEARM_SPORTS.get(sport)
            if not sport_info:
                logger.warning(f"Unknown sidearm sport code '{sport}' for {stats_url}")
                return

            url = build_sidearm_game_json_url(stats_url, sport)
            if not url:
                return

            params = {
                "detail": "full"
            }

            # Build on the shared headers; this endpoint returns JSON and wants
            # the stats page as the referer.
            headers = {
                **HTTP_REQUEST_HEADERS,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": stats_url,
            }

            try:
                r = get_with_retries(url, params=params, headers=headers, timeout=10)
                game_data = r.json()
            except Exception as e:
                logger.error(f"Failed to fetch live game data from {url}: {str(e)}")
                return

            game_data["sport_code"] = sport
            game_data["sport_info"] = sport_info


            matching_game = GameService.find_matching_game(game_data)
            if matching_game:
                game_id = matching_game.id
                game_info = game_data.get('Game') or {}

                # A finished game we have already settled needs no further
                # polling: its score cannot change, and re-broadcasting it
                # every 30 seconds told subscribers it was still live.
                if game_info.get('IsComplete') and not matching_game.is_live and matching_game.result:
                    logger.debug('Skipping completed game %s', game_id)
                    return

                # is_live, last_updated and result are written here too, so a
                # game that has just ended gets one last update instead of
                # being left flagged live for good.
                was_updated = GameService.update_game_with_new_data(matching_game, game_data)
                if was_updated:
                    # Refresh the game object
                    matching_game = GameService.get_game_by_id(game_id)

                    # Notify subscribers
                    try:
                        from src.websocket_manager import get_websocket_manager
                        websocket_manager = get_websocket_manager()
                        subscriber_count = websocket_manager.get_game_subscriber_count(game_id)
                        logger.info(f"Notifying {subscriber_count} subscribers of game {game_id} update")

                        update_data = {
                            'gameId': game_id,
                            'isLive': bool(matching_game.is_live),
                            'isComplete': bool(game_info.get('IsComplete')),
                            'lastUpdated': datetime.now(timezone.utc).isoformat(),
                            'boxScore': matching_game.box_score,
                            'scoreBreakdown': matching_game.score_breakdown,
                            'result': matching_game.result,
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
        
        # Try to find matching game. Prefer the sport_info resolved by the caller,
        # since a game.json can omit GlobalSportShortname.
        sport_info = game_data.get('sport_info') or SIDEARM_SPORTS.get(
            game.get('GlobalSportShortname', '')
        )
        if not sport_info:
            logger.warning(
                f"Unknown sidearm sport code '{game.get('GlobalSportShortname', '')}'"
            )
            return None
        sport, gender = sport_info['sport'], sport_info['gender']
        
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
        existing_ids = {
            play.get('play_id') for play in existing_plays if play.get('play_id')
        }

        for new_play in new_plays:
            play_id = new_play.get('play_id')
            if play_id:
                is_duplicate = play_id in existing_ids
            else:
                is_duplicate = any(
                    new_play.get('description') == existing_play.get('description') and
                    new_play.get('time') == existing_play.get('time') and
                    new_play.get('period') == existing_play.get('period')
                    for existing_play in existing_plays
                )

            if not is_duplicate:
                unique_plays.append(new_play)
                if play_id:
                    existing_ids.add(play_id)

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
        cornell_is_home = home_team.get('Name', '').upper() == 'CORNELL'
        cor_team = home_team if cornell_is_home else visiting_team
        opp_team = visiting_team if cornell_is_home else home_team
        cor_period_scores = cor_team.get('PeriodScores', [])
        opp_period_scores = opp_team.get('PeriodScores', [])

        # Convert to our format
        score_breakdown = [[], []]
        for i in range(len(cor_period_scores)):
            score_breakdown[0].append(str(cor_period_scores[i]))
            score_breakdown[1].append(str(opp_period_scores[i]) if i < len(opp_period_scores) else "0")

        score_breakdown[0].extend(GameService.breakdown_totals(cor_team, game.sport))
        score_breakdown[1].extend(GameService.breakdown_totals(opp_team, game.sport))

        return score_breakdown

    def breakdown_totals(team: Dict, sport: Optional[str]) -> List[str]:
        """
        The cells that follow the per-period scores in a stored breakdown.

        Most sports end with the game total. Baseball and softball box scores
        end with runs, hits and errors, so a live breakdown has to as well or
        the clients read errors as the score. Volleyball needs no special case:
        its Score is sets won, which is exactly what its result ('W,3-1')
        counts, so the plain total is already right.
        """
        total = str(team.get('Score', 0))
        if (sport or '').lower() in ('baseball', 'softball'):
            hits, errors = team.get('Hits'), team.get('Errors')
            if hits is not None and errors is not None:
                return [total, str(hits), str(errors)]
        return [total]
    
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

        # Prefer the full play log, which arrives oldest-first and holds every play
        # of the game. Game.LastPlays only carries the most recent five, so a poll
        # interval busier than that would silently drop plays. Re-sending the whole
        # log each poll is safe because plays are de-duplicated by their Sidearm id.
        plays = game_data.get('Plays')
        if not plays:
            # LastPlays arrives newest-first, so reverse it to stay chronological.
            plays = list(reversed(game.get('LastPlays') or []))

        converted_plays = []
        # Plays arrive oldest-first, so the running score carries forward and
        # lets convert_play_to_our_format name the team on the plays Sidearm
        # sends unattributed.
        previous_score = None
        for play in plays:
            converted_play = convert_play_to_our_format(play, game, previous_score)
            if converted_play:
                converted_plays.append(converted_play)
            if isinstance(play.get('Score'), dict):
                previous_score = play['Score']

        return converted_plays

    def result_from_live_data(game_data: Dict) -> Optional[str]:
        """
        Cornell's result in the stored "W,4-2" form, or None if not known yet.

        Only filled in once Sidearm says the game is complete: a W written at
        half time would be wrong for as long as the lead held.
        """
        game_info = (game_data or {}).get('Game') or {}
        if not game_info.get('IsComplete'):
            return None

        home_team = game_info.get('HomeTeam') or {}
        visiting_team = game_info.get('VisitingTeam') or {}
        cornell_is_home = (home_team.get('Name') or '').upper() == 'CORNELL'
        cor_score = (home_team if cornell_is_home else visiting_team).get('Score')
        opp_score = (visiting_team if cornell_is_home else home_team).get('Score')
        if cor_score is None or opp_score is None:
            return None

        outcome = 'W' if cor_score > opp_score else 'L' if cor_score < opp_score else 'T'
        return f"{outcome},{cor_score}-{opp_score}"

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
            existing_box_score = game.box_score or []
            new_plays = GameService.get_game_plays(game_data)
            unique_plays = GameService.filter_duplicate_plays(existing_box_score, new_plays)

            update_data = {}
            if unique_plays:
                update_data['box_score'] = existing_box_score + unique_plays

            # Recomputed every poll rather than only when a play arrives. The
            # last poll of a game usually brings no new play, and that is
            # exactly the poll that has to carry the final score, write the
            # result and clear is_live.
            score_breakdown = GameService.update_score_breakdown(game_data, game)
            if score_breakdown != (game.score_breakdown or []):
                update_data['score_breakdown'] = score_breakdown

            result = GameService.result_from_live_data(game_data)
            if result and result != game.result:
                update_data['result'] = result

            is_live = is_game_active(game_data)
            if is_live != bool(game.is_live):
                update_data['is_live'] = is_live

            if not update_data:
                return False

            update_data['last_updated'] = datetime.now(timezone.utc).isoformat()
            GameService.update_game(game.id, update_data)
            logger.info(
                "Updated game %s: %d new play(s), fields %s",
                game.id,
                len(unique_plays),
                sorted(field for field in update_data if field != 'last_updated'),
            )

            return True
            
        except Exception as e:
            logger.error(f"Error updating game {game.id}: {str(e)}")
            return False