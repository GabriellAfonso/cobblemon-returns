import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_ranking_image(png_bytes: bytes, filename: str) -> str | None:
    """POST image to Discord webhook. Returns message_id or None."""
    if not getattr(settings, 'DISCORD_WEBHOOK_URL', ''):
        logger.warning("DISCORD_WEBHOOK_URL not configured — skipping send")
        return None

    url = f"{settings.DISCORD_WEBHOOK_URL}?wait=true"
    try:
        resp = requests.post(url, files={'file': (filename, png_bytes, 'image/png')}, timeout=15)
        if resp.ok:
            return resp.json().get('id')
        logger.error("Discord webhook POST failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.error("Discord webhook request error: %s", e)
    return None


def delete_discord_message(message_id: str) -> None:
    """Delete a previously posted webhook message."""
    if not getattr(settings, 'DISCORD_WEBHOOK_URL', '') or not message_id:
        return
    url = f"{settings.DISCORD_WEBHOOK_URL}/messages/{message_id}"
    try:
        requests.delete(url, timeout=10)
    except Exception as e:
        logger.error("Failed to delete Discord message %s: %s", message_id, e)
