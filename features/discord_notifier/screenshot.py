import base64
import logging

from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "svg": "image/svg+xml",
}


def _icon_data_uri(icon_img_path: str) -> str:
    if not icon_img_path:
        return ""
    from django.contrib.staticfiles import finders

    file_path = finders.find(icon_img_path)
    if not file_path:
        return ""
    ext = icon_img_path.rsplit(".", 1)[-1].lower()
    mime = _MIME.get(ext, "image/png")
    with open(file_path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def render_ranking_screenshot(
    ranking_config: dict, players: list[dict], date_str: str
) -> bytes:
    from django.conf import settings

    ranking_ctx = {
        **ranking_config,
        "icon_data_uri": _icon_data_uri(ranking_config.get("icon_img", "")),
    }

    html = render_to_string(
        "rankings/discord_card.html",
        {
            "ranking": ranking_ctx,
            "players": players,
            "date": date_str,
            "SERVER_HOST": getattr(settings, "SERVER_HOST", ""),
        },
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 520, "height": 600})
            page.set_content(html)
            page.wait_for_load_state("networkidle")
            return page.screenshot(full_page=True)
        finally:
            browser.close()
