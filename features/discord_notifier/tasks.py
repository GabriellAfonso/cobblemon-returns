import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

discord_scheduler = BackgroundScheduler()


def post_all_rankings() -> None:
    """
    For each ranking in RANKINGS:
    1. Query top 10 players
    2. Render screenshot
    3. Delete previous message if exists
    4. Post new image, save message_id
    """
    from django.utils import timezone

    from features.discord_notifier.repositories.message_repository import (
        DiscordMessageRepository,
    )
    from features.discord_notifier.screenshot import render_ranking_screenshot
    from features.discord_notifier.webhook import (
        delete_discord_message,
        send_ranking_image,
    )
    from features.players.repositories.stats_repository import PlayerStatsRepository
    from features.rankings.config import RANKINGS
    from features.rankings.formatters import format_value

    stats_repo = PlayerStatsRepository()
    message_repo = DiscordMessageRepository()
    date_str = timezone.localtime().strftime("%d/%m/%Y · %H:%M")

    for r in RANKINGS:
        try:
            top10 = stats_repo.get_top_by_field(r["field"])
            players = [
                {
                    "name": stat.player.username,
                    "value": format_value(getattr(stat, r["field"]), r["format"]),
                }
                for stat in top10
            ]

            png = render_ranking_screenshot(r, players, date_str)

            existing = message_repo.get_by_ranking(r["id"])
            if existing:
                delete_discord_message(existing.message_id, r)

            message_id = send_ranking_image(png, f"ranking_{r['id']}.png", r)
            if message_id:
                message_repo.update_or_create(r["id"], message_id)
        except Exception as e:
            logger.error("Failed to post ranking %s: %s", r["id"], e)


def schedule_discord_posts() -> None:
    """Add daily job at DISCORD_RANKING_HOUR. Called from AppConfig.ready()."""
    if discord_scheduler.running:
        return
    hour = int(getattr(settings, "DISCORD_RANKING_HOUR", 20))
    discord_scheduler.add_job(
        post_all_rankings,
        "cron",
        hour=hour,
        minute=0,
        id="discord_rankings",
        replace_existing=True,
    )
    discord_scheduler.start()
    logger.info("Discord scheduler started (hour: %d:00)", hour)
