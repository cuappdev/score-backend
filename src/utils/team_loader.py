from promise import Promise
from promise.dataloader import DataLoader
from src.services import TeamService

class TeamLoader(DataLoader):
    def batch_load_fn(self, team_ids):
        teams = TeamService.get_teams_by_ids(team_ids)
        team_map = {team.id: team for team in teams}
        return Promise.resolve([team_map.get(team_id) for team_id in team_ids])