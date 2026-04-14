import logging

from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def render_ranking_screenshot(ranking_config, players, date_str):
    """
    Render the discord_card.html template with given data,
    take a screenshot, and return the PNG bytes.
    """
    from django.conf import settings

    html = render_to_string('rankings/discord_card.html', {
        'ranking': ranking_config,
        'players': players,
        'date': date_str,
        'SERVER_HOST': getattr(settings, 'SERVER_HOST', ''),
    })

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 520, 'height': 600})
            page.set_content(html)
            page.wait_for_load_state('networkidle')
            return page.screenshot(full_page=True)
        finally:
            browser.close()
