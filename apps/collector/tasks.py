import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_collection():
    """Fetch data from SFTP and update all PlayerStats records."""
    from apps.collector.models import CollectionLog
    from apps.collector.sftp import collect_player_data, get_sftp_client, read_usercache
    from apps.players.models import Player, PlayerStats

    if not getattr(settings, 'SFTP_HOST', ''):
        logger.warning("SFTP_HOST not configured — skipping collection")
        CollectionLog.objects.create(
            status=CollectionLog.STATUS_ERROR,
            message="SFTP_HOST not configured",
        )
        return

    sftp = None
    try:
        sftp = get_sftp_client()

        # Discover players by listing the Minecraft stats directory
        stats_dir = f"{settings.MINECRAFT_WORLD_PATH}/stats"
        stat_files = sftp.listdir(stats_dir)
        uuids = [f.replace('.json', '') for f in stat_files if f.endswith('.json')]

        usercache = read_usercache(sftp)

        updated = 0
        for uuid in uuids:
            try:
                stat_data = collect_player_data(sftp, uuid)
                username = usercache.get(uuid, uuid)
                player, _ = Player.objects.get_or_create(uuid=uuid, defaults={'username': username})
                if player.username != username and username != uuid:
                    player.username = username
                player.last_seen = timezone.now()
                player.save(update_fields=['username', 'last_seen'])

                PlayerStats.objects.update_or_create(
                    player=player,
                    defaults=stat_data,
                )
                updated += 1
            except Exception as e:
                logger.error("Failed to update player %s: %s", uuid, e)

        CollectionLog.objects.create(
            status=CollectionLog.STATUS_OK,
            players_updated=updated,
        )
        logger.info("Collection complete: %d players updated", updated)

    except Exception as e:
        logger.error("Collection failed: %s", e)
        CollectionLog.objects.create(
            status=CollectionLog.STATUS_ERROR,
            message=str(e),
        )
    finally:
        if sftp:
            sftp.get_channel().get_transport().close()


def start_scheduler():
    """Start APScheduler. Called once from AppConfig.ready()."""
    if scheduler.running:
        return
    interval = int(getattr(settings, 'COLLECTOR_INTERVAL_MINUTES', 15))
    scheduler.add_job(run_collection, 'interval', minutes=interval, id='collect', replace_existing=True)
    scheduler.start()
    logger.info("Collector scheduler started (interval: %d min)", interval)
