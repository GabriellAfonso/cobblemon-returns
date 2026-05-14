from unittest.mock import ANY, MagicMock, patch

from django.db import IntegrityError
from django.test import RequestFactory, TestCase, override_settings, tag

from features.discord_notifier.models import DiscordPostedMessage
from features.discord_notifier.repositories.message_repository import (
    DiscordMessageRepository,
)
from features.players.models import Player, PlayerStats

WEBHOOK_SETTINGS = {
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/token",
    "DISCORD_RANKING_HOUR": 20,
}


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("unit")
@override_settings(**WEBHOOK_SETTINGS)
class SendRankingImageTest(TestCase):
    @patch("features.discord_notifier.webhook.requests.post")
    def test_returns_message_id_on_success(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"id": "999888777"})
        from features.discord_notifier.webhook import send_ranking_image

        result = send_ranking_image(b"fake-png", "test.png", {})
        self.assertEqual(result, "999888777")

    @patch("features.discord_notifier.webhook.requests.post")
    def test_posts_to_webhook_url_with_wait(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"id": "111"})
        from features.discord_notifier.webhook import send_ranking_image

        send_ranking_image(b"fake-png", "ranking_hours.png", {})
        called_url = mock_post.call_args[0][0]
        self.assertIn("?wait=true", called_url)

    @patch("features.discord_notifier.webhook.requests.post")
    def test_returns_none_on_http_error(self, mock_post):
        mock_post.return_value = MagicMock(
            ok=False, status_code=400, text="Bad Request"
        )
        from features.discord_notifier.webhook import send_ranking_image

        result = send_ranking_image(b"fake-png", "test.png", {})
        self.assertIsNone(result)

    def test_returns_none_when_webhook_url_empty(self):
        with self.settings(DISCORD_WEBHOOK_URL=""):
            from features.discord_notifier.webhook import send_ranking_image

            result = send_ranking_image(b"fake-png", "test.png", {})
        self.assertIsNone(result)


@tag("unit")
@override_settings(**WEBHOOK_SETTINGS)
class DeleteDiscordMessageTest(TestCase):
    @patch("features.discord_notifier.webhook.requests.delete")
    def test_delete_calls_correct_url(self, mock_delete):
        from features.discord_notifier.webhook import delete_discord_message

        delete_discord_message("abc123", {})
        called_url = mock_delete.call_args[0][0]
        self.assertIn("/messages/abc123", called_url)

    @patch("features.discord_notifier.webhook.requests.delete")
    def test_delete_skips_when_no_message_id(self, mock_delete):
        from features.discord_notifier.webhook import delete_discord_message

        delete_discord_message(None, {})
        mock_delete.assert_not_called()


@tag("integration")
@override_settings(**WEBHOOK_SETTINGS)
class PostAllRankingsTest(TestCase):
    def setUp(self):
        _make_player(
            "uuid-1",
            "AshKetchum",
            play_time_ticks=72000,
            pokemons_caught=50,
            pokedex_registered=30,
            cobbletcg_cards=10,
            battles_won=20,
            cobbledollars=1000,
        )

    @patch(
        "features.discord_notifier.screenshot.render_ranking_screenshot",
        return_value=b"fake-png",
    )
    @patch(
        "features.discord_notifier.webhook.send_ranking_image", return_value="msg-001"
    )
    @patch("features.discord_notifier.webhook.delete_discord_message")
    def test_saves_message_id_for_each_ranking(
        self, mock_delete, mock_send, mock_screenshot
    ):
        from features.discord_notifier.tasks import post_all_rankings
        from features.rankings.config import RANKINGS

        post_all_rankings()
        self.assertEqual(DiscordPostedMessage.objects.count(), len(RANKINGS))

    @patch(
        "features.discord_notifier.screenshot.render_ranking_screenshot",
        return_value=b"fake-png",
    )
    @patch(
        "features.discord_notifier.webhook.send_ranking_image", return_value="msg-new"
    )
    @patch("features.discord_notifier.webhook.delete_discord_message")
    def test_deletes_previous_message_when_exists(
        self, mock_delete, mock_send, mock_screenshot
    ):
        DiscordPostedMessage.objects.create(ranking_id="hours", message_id="old-msg-id")
        from features.discord_notifier.tasks import post_all_rankings

        post_all_rankings()
        mock_delete.assert_any_call("old-msg-id", ANY)

    @patch(
        "features.discord_notifier.screenshot.render_ranking_screenshot",
        return_value=b"fake-png",
    )
    @patch("features.discord_notifier.webhook.send_ranking_image", return_value=None)
    @patch("features.discord_notifier.webhook.delete_discord_message")
    def test_no_db_entry_when_send_fails(self, mock_delete, mock_send, mock_screenshot):
        from features.discord_notifier.tasks import post_all_rankings

        post_all_rankings()
        self.assertEqual(DiscordPostedMessage.objects.count(), 0)


@tag("unit")
class DiscordPostedMessageModelTest(TestCase):
    def test_str_representation(self):
        msg = DiscordPostedMessage.objects.create(
            ranking_id="hours", message_id="abc123"
        )
        self.assertEqual(str(msg), "hours → abc123")

    def test_ranking_id_unique_constraint(self):
        DiscordPostedMessage.objects.create(ranking_id="hours", message_id="first")
        with self.assertRaises(IntegrityError):
            DiscordPostedMessage.objects.create(ranking_id="hours", message_id="second")

    def test_posted_at_is_set_on_create(self):
        msg = DiscordPostedMessage.objects.create(
            ranking_id="catches", message_id="xyz"
        )
        self.assertIsNotNone(msg.posted_at)


@tag("unit")
class DiscordMessageRepositoryTest(TestCase):
    def setUp(self):
        self.repo = DiscordMessageRepository()

    def test_get_by_ranking_returns_existing(self):
        DiscordPostedMessage.objects.create(ranking_id="hours", message_id="msg-1")
        result = self.repo.get_by_ranking("hours")
        self.assertIsNotNone(result)
        self.assertEqual(result.message_id, "msg-1")

    def test_get_by_ranking_returns_none_when_missing(self):
        result = self.repo.get_by_ranking("does-not-exist")
        self.assertIsNone(result)

    def test_update_or_create_creates_new(self):
        obj = self.repo.update_or_create("catches", "new-msg")
        self.assertEqual(obj.ranking_id, "catches")
        self.assertEqual(obj.message_id, "new-msg")
        self.assertEqual(DiscordPostedMessage.objects.count(), 1)

    def test_update_or_create_updates_existing(self):
        DiscordPostedMessage.objects.create(ranking_id="catches", message_id="old-msg")
        self.repo.update_or_create("catches", "new-msg")
        self.assertEqual(DiscordPostedMessage.objects.count(), 1)
        self.assertEqual(
            DiscordPostedMessage.objects.get(ranking_id="catches").message_id, "new-msg"
        )


@tag("integration")
class DiscordCardViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_discord_card_returns_200(self):
        from features.discord_notifier.views import discord_card_preview

        request = self.factory.get("/")
        resp = discord_card_preview(request, ranking_id="hours")
        self.assertEqual(resp.status_code, 200)

    def test_discord_card_renders_card_html(self):
        from features.discord_notifier.views import discord_card_preview

        request = self.factory.get("/")
        resp = discord_card_preview(request, ranking_id="hours")
        self.assertIn(b"COBBLEMON", resp.content)

    def test_discord_card_accepts_custom_ranking_id(self):
        from features.discord_notifier.views import discord_card_preview

        request = self.factory.get("/")
        resp = discord_card_preview(request, ranking_id="catches")
        self.assertEqual(resp.status_code, 200)
