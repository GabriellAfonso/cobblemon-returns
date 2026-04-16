import logging

from django.conf import settings
from django.utils import timezone

from features.collector.models import CollectionLog
from features.collector.repositories.log_repository import CollectionLogRepository
from features.collector.sftp import collect_player_data, get_sftp_client, read_usercache
from features.players.repositories.player_repository import PlayerRepository
from features.players.repositories.stats_repository import PlayerStatsRepository

logger = logging.getLogger(__name__)


class CollectionService:
    def __init__(
        self,
        player_repo: PlayerRepository,
        stats_repo: PlayerStatsRepository,
        log_repo: CollectionLogRepository,
    ):
        self.player_repo = player_repo
        self.stats_repo = stats_repo
        self.log_repo = log_repo

    def run(self) -> None:
        if not getattr(settings, "SFTP_HOST", ""):
            logger.warning("SFTP_HOST not configured — skipping collection")
            self.log_repo.create(
                status=CollectionLog.STATUS_ERROR, message="SFTP_HOST not configured"
            )
            return

        sftp = None
        try:
            sftp = get_sftp_client()

            stats_dir = f"{settings.MINECRAFT_WORLD_PATH}/stats"
            stat_files = sftp.listdir(stats_dir)
            uuids = [f.replace(".json", "") for f in stat_files if f.endswith(".json")]

            usercache = read_usercache(sftp)

            updated = 0
            for uuid in uuids:
                try:
                    stat_data = collect_player_data(sftp, uuid)
                    username = usercache.get(uuid, uuid)
                    player, _ = self.player_repo.get_or_create(uuid, username)
                    if player.username != username and username != uuid:
                        player.username = username
                    player.last_seen = timezone.now()
                    player.save(update_fields=["username", "last_seen"])

                    self.stats_repo.update_or_create(player, stat_data)
                    updated += 1
                except Exception as e:
                    logger.error("Failed to update player %s: %s", uuid, e)

            self.log_repo.create(
                status=CollectionLog.STATUS_OK, players_updated=updated
            )
            logger.info("Collection complete: %d players updated", updated)

        except Exception as e:
            logger.error("Collection failed: %s", e)
            self.log_repo.create(status=CollectionLog.STATUS_ERROR, message=str(e))
        finally:
            if sftp:
                sftp.get_channel().get_transport().close()
