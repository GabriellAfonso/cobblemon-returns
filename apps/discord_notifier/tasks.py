import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

logger = logging.getLogger(__name__)

discord_scheduler = BackgroundScheduler()


def post_all_rankings():
    """
    For each ranking in RANKINGS:
    1. Query top 10 players
    2. Render screenshot
    3. Delete previous message if exists
    4. Post new image, save message_id
    """
    from django.utils import timezone

    from apps.discord_notifier.models import DiscordPostedMessage
    from apps.discord_notifier.screenshot import render_ranking_screenshot
    from apps.discord_notifier.webhook import delete_discord_message, send_ranking_image
    from apps.players.models import PlayerStats
    from apps.rankings.config import RANKINGS
    from apps.rankings.formatters import format_value

    date_str = timezone.now().strftime('%d/%m/%Y · %H:%M')

    for r in RANKINGS:
        try:
            top10 = list(
                PlayerStats.objects.order_by(f'-{r["field"]}')
                .select_related('player')[:10]
            )
            players = [
                {
                    'name': stat.player.username,
                    'value': format_value(getattr(stat, r['field']), r['format']),
                }
                for stat in top10
            ]

            png = render_ranking_screenshot(r, players, date_str)

            try:
                existing = DiscordPostedMessage.objects.get(ranking_id=r['id'])
                delete_discord_message(existing.message_id)
            except DiscordPostedMessage.DoesNotExist:
                pass

            message_id = send_ranking_image(png, f"ranking_{r['id']}.png")
            if message_id:
                DiscordPostedMessage.objects.update_or_create(
                    ranking_id=r['id'],
                    defaults={'message_id': message_id},
                )
        except Exception as e:
            logger.error("Failed to post ranking %s: %s", r['id'], e)


def schedule_discord_posts():
    """Add daily job at DISCORD_RANKING_HOUR. Called from AppConfig.ready()."""
    if discord_scheduler.running:
        return
    hour = int(getattr(settings, 'DISCORD_RANKING_HOUR', 20))
    discord_scheduler.add_job(
        post_all_rankings,
        'cron',
        hour=hour,
        minute=0,
        id='discord_rankings',
        replace_existing=True,
    )
    discord_scheduler.start()
    logger.info("Discord scheduler started (hour: %d:00)", hour)
