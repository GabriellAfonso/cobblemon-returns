import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_collection() -> None:
    """Fetch data from SFTP and update all PlayerStats records."""
    from features.collector.repositories.log_repository import CollectionLogRepository
    from features.collector.services.collection_service import CollectionService
    from features.players.repositories.player_repository import PlayerRepository
    from features.players.repositories.stats_repository import PlayerStatsRepository

    CollectionService(
        player_repo=PlayerRepository(),
        stats_repo=PlayerStatsRepository(),
        log_repo=CollectionLogRepository(),
    ).run()


def start_scheduler() -> None:
    """Start APScheduler. Called once from AppConfig.ready()."""
    if scheduler.running:
        return
    interval = int(getattr(settings, "COLLECTOR_INTERVAL_MINUTES", 15))
    scheduler.add_job(
        run_collection,
        "interval",
        minutes=interval,
        id="collect",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Collector scheduler started (interval: %d min)", interval)
