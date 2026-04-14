from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.discord_notifier.models import DiscordPostedMessage
from apps.players.models import Player, PlayerStats

WEBHOOK_SETTINGS = {
    'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/123/token',
    'DISCORD_RANKING_HOUR': 20,
}


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@override_settings(**WEBHOOK_SETTINGS)
class SendRankingImageTest(TestCase):

    @patch('apps.discord_notifier.webhook.requests.post')
    def test_returns_message_id_on_success(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {'id': '999888777'})
        from apps.discord_notifier.webhook import send_ranking_image
        result = send_ranking_image(b'fake-png', 'test.png')
        self.assertEqual(result, '999888777')

    @patch('apps.discord_notifier.webhook.requests.post')
    def test_posts_to_webhook_url_with_wait(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {'id': '111'})
        from apps.discord_notifier.webhook import send_ranking_image
        send_ranking_image(b'fake-png', 'ranking_hours.png')
        called_url = mock_post.call_args[0][0]
        self.assertIn('?wait=true', called_url)

    @patch('apps.discord_notifier.webhook.requests.post')
    def test_returns_none_on_http_error(self, mock_post):
        mock_post.return_value = MagicMock(ok=False, status_code=400, text='Bad Request')
        from apps.discord_notifier.webhook import send_ranking_image
        result = send_ranking_image(b'fake-png', 'test.png')
        self.assertIsNone(result)

    def test_returns_none_when_webhook_url_empty(self):
        with self.settings(DISCORD_WEBHOOK_URL=''):
            from apps.discord_notifier.webhook import send_ranking_image
            result = send_ranking_image(b'fake-png', 'test.png')
        self.assertIsNone(result)


@override_settings(**WEBHOOK_SETTINGS)
class DeleteDiscordMessageTest(TestCase):

    @patch('apps.discord_notifier.webhook.requests.delete')
    def test_delete_calls_correct_url(self, mock_delete):
        from apps.discord_notifier.webhook import delete_discord_message
        delete_discord_message('abc123')
        called_url = mock_delete.call_args[0][0]
        self.assertIn('/messages/abc123', called_url)

    @patch('apps.discord_notifier.webhook.requests.delete')
    def test_delete_skips_when_no_message_id(self, mock_delete):
        from apps.discord_notifier.webhook import delete_discord_message
        delete_discord_message(None)
        mock_delete.assert_not_called()


@override_settings(**WEBHOOK_SETTINGS)
class PostAllRankingsTest(TestCase):

    def setUp(self):
        _make_player('uuid-1', 'AshKetchum', play_time_ticks=72000, pokemons_caught=50,
                     pokedex_registered=30, cobbletcg_cards=10, battles_won=20, cobbledollars=1000)

    @patch('apps.discord_notifier.screenshot.render_ranking_screenshot', return_value=b'fake-png')
    @patch('apps.discord_notifier.webhook.send_ranking_image', return_value='msg-001')
    @patch('apps.discord_notifier.webhook.delete_discord_message')
    def test_saves_message_id_for_each_ranking(self, mock_delete, mock_send, mock_screenshot):
        from apps.discord_notifier.tasks import post_all_rankings
        from apps.rankings.config import RANKINGS
        post_all_rankings()
        self.assertEqual(DiscordPostedMessage.objects.count(), len(RANKINGS))

    @patch('apps.discord_notifier.screenshot.render_ranking_screenshot', return_value=b'fake-png')
    @patch('apps.discord_notifier.webhook.send_ranking_image', return_value='msg-new')
    @patch('apps.discord_notifier.webhook.delete_discord_message')
    def test_deletes_previous_message_when_exists(self, mock_delete, mock_send, mock_screenshot):
        DiscordPostedMessage.objects.create(ranking_id='hours', message_id='old-msg-id')
        from apps.discord_notifier.tasks import post_all_rankings
        post_all_rankings()
        mock_delete.assert_any_call('old-msg-id')

    @patch('apps.discord_notifier.screenshot.render_ranking_screenshot', return_value=b'fake-png')
    @patch('apps.discord_notifier.webhook.send_ranking_image', return_value=None)
    @patch('apps.discord_notifier.webhook.delete_discord_message')
    def test_no_db_entry_when_send_fails(self, mock_delete, mock_send, mock_screenshot):
        from apps.discord_notifier.tasks import post_all_rankings
        post_all_rankings()
        self.assertEqual(DiscordPostedMessage.objects.count(), 0)
