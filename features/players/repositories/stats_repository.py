import datetime

from features.players.models import Player, PlayerStats


class PlayerStatsRepository:
    def get_leader_by_field(self, field: str) -> PlayerStats | None:
        return (
            PlayerStats.objects.order_by(f"-{field}").select_related("player").first()
        )

    def get_top_by_field(self, field: str, n: int = 10) -> list[PlayerStats]:
        return list(
            PlayerStats.objects.order_by(f"-{field}").select_related("player")[:n]
        )

    def get_last_updated(self) -> datetime.datetime | None:
        return (
            PlayerStats.objects.order_by("-updated_at")
            .values_list("updated_at", flat=True)
            .first()
        )

    def update_or_create(self, player: Player, data: dict[str, int]) -> PlayerStats:
        stats, _ = PlayerStats.objects.update_or_create(player=player, defaults=data)
        return stats
