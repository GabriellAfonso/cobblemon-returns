from django.db.models import QuerySet

from features.players.models import Player


class PlayerRepository:
    def count(self) -> int:
        return Player.objects.count()

    def get_or_create(self, uuid: str, username: str) -> tuple[Player, bool]:
        return Player.objects.get_or_create(uuid=uuid, defaults={"username": username})

    def get_all_with_stats(self, sort_field: str | None = None) -> QuerySet:
        qs = Player.objects.select_related("stats").order_by("username")
        if sort_field:
            qs = qs.order_by(f"-stats__{sort_field}")
        return qs
