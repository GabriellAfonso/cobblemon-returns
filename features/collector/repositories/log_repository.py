from django.db.models import QuerySet

from features.collector.models import CollectionLog


class CollectionLogRepository:
    def create(
        self, status: str, message: str = "", players_updated: int = 0
    ) -> CollectionLog:
        return CollectionLog.objects.create(
            status=status,
            message=message,
            players_updated=players_updated,
        )

    def get_latest(self) -> CollectionLog | None:
        return CollectionLog.objects.first()  # ordered by -timestamp via Meta

    def get_last_n(self, n: int) -> QuerySet:
        return CollectionLog.objects.all()[:n]
