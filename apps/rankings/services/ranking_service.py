import datetime

from apps.players.repositories.stats_repository import PlayerStatsRepository
from apps.rankings.config import RANKINGS
from apps.rankings.formatters import format_value


class RankingService:

    def __init__(self, stats_repo: PlayerStatsRepository):
        self.stats_repo = stats_repo

    def get_home_leaders(self) -> list[dict]:
        leaders = []
        for r in RANKINGS:
            top = self.stats_repo.get_leader_by_field(r['field'])
            if top:
                leaders.append({
                    'id': r['id'],
                    'label': r['label'],
                    'icon': r['icon'],
                    'player_name': top.player.username,
                    'value': format_value(getattr(top, r['field']), r['format']),
                })
        return leaders

    def get_full_rankings(self) -> tuple[list[dict], datetime.datetime | None]:
        rankings = []
        for r in RANKINGS:
            top10 = self.stats_repo.get_top_by_field(r['field'])
            max_val = getattr(top10[0], r['field']) if top10 else 1
            players = []
            for stat in top10:
                raw = getattr(stat, r['field'])
                players.append({
                    'name': stat.player.username,
                    'raw_value': raw,
                    'value': format_value(raw, r['format']),
                    'bar_pct': round((raw / max_val) * 100) if max_val else 0,
                })
            rankings.append({**r, 'players': players})
        return rankings, self.stats_repo.get_last_updated()
