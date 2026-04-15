from django.db.models import QuerySet

from apps.collector.repositories.log_repository import CollectionLogRepository
from apps.players.repositories.player_repository import PlayerRepository


class DashboardService:

    def __init__(self, player_repo: PlayerRepository, log_repo: CollectionLogRepository):
        self.player_repo = player_repo
        self.log_repo = log_repo

    def get_summary(self) -> dict:
        return {
            'total_players': self.player_repo.count(),
            'last_log': self.log_repo.get_latest(),
        }

    def get_players(self, sort_field: str | None = None) -> QuerySet:
        return self.player_repo.get_all_with_stats(sort_field)

    def get_logs(self, n: int) -> QuerySet:
        return self.log_repo.get_last_n(n)
