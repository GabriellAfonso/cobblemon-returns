import logging
import os

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _resolve_webhook_url(ranking_config: dict) -> str:
    env_key = ranking_config.get("webhook_env")
    if env_key:
        url = os.environ.get(env_key, "")
        if url:
            return url
    return getattr(settings, "DISCORD_WEBHOOK_URL", "")


def send_ranking_image(
    png_bytes: bytes, filename: str, ranking_config: dict
) -> str | None:
    """POST image to Discord webhook for given ranking. Returns message_id or None."""
    webhook_url = _resolve_webhook_url(ranking_config)
    if not webhook_url:
        logger.warning(
            "No webhook URL for ranking %s — skipping", ranking_config.get("id")
        )
        return None

    try:
        resp = requests.post(
            f"{webhook_url}?wait=true",
            files={"file": (filename, png_bytes, "image/png")},
            timeout=15,
        )
        if resp.ok:
            return resp.json().get("id")
        logger.error("Discord webhook POST failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.error("Discord webhook request error: %s", e)
    return None


def delete_discord_message(message_id: str, ranking_config: dict) -> None:
    """Delete a previously posted webhook message."""
    webhook_url = _resolve_webhook_url(ranking_config)
    if not webhook_url or not message_id:
        return
    try:
        requests.delete(f"{webhook_url}/messages/{message_id}", timeout=10)
    except Exception as e:
        logger.error("Failed to delete Discord message %s: %s", message_id, e)
