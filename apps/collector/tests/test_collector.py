from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.collector.models import CollectionLog
from apps.collector.sftp import collect_player_data
from apps.players.models import Player, PlayerStats

SFTP_SETTINGS = {
    'SFTP_HOST': 'sftp.example.com',
    'SFTP_PORT': '22',
    'SFTP_USER': 'user',
    'SFTP_KEY_PATH': '/tmp/key',
    'MINECRAFT_WORLD_PATH': '/world',
    'COBBLEMON_DATA_PATH': '/cobblemon',
    'COBBLE_ECONOMY_PATH': '/economy',
    'COBBLE_TCG_PATH': '/tcg',
    'COLLECTOR_INTERVAL_MINUTES': 15,
}


def _make_sftp(stats_json=None, cobblemon_json=None, economy_json=None,
               pokemon_count=5, tcg_count=3):
    """Build a MagicMock SFTP client with configurable file responses."""
    import json

    sftp = MagicMock()

    def fake_open(path):
        if path.endswith('/stats/test-uuid.json'):
            content = stats_json or {'stats': {'minecraft:custom': {'minecraft:play_time': 72000}}}
        elif path.endswith('/data.json'):
            content = cobblemon_json or {'caughtPokemon': 150, 'battleWins': 42}
        elif path.endswith('.json'):
            content = economy_json or {'balance': 1000}
        else:
            raise FileNotFoundError(path)

        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(content).encode()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        return mock_file

    sftp.open.side_effect = fake_open
    sftp.listdir.side_effect = lambda path: (
        [f'{i}.json' for i in range(pokemon_count)] if 'pokemon' in path
        else [f'card{i}.json' for i in range(tcg_count)]
    )
    return sftp


@override_settings(**SFTP_SETTINGS)
class CollectPlayerDataTest(TestCase):

    def test_returns_all_stat_keys(self):
        sftp = _make_sftp()
        result = collect_player_data(sftp, 'test-uuid')
        expected_keys = {
            'play_time_ticks', 'pokemons_caught', 'pokedex_registered',
            'cobbletcg_cards', 'battles_won', 'cobbledollars',
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_reads_play_time(self):
        sftp = _make_sftp(stats_json={'stats': {'minecraft:custom': {'minecraft:play_time': 36000}}})
        result = collect_player_data(sftp, 'test-uuid')
        self.assertEqual(result['play_time_ticks'], 36000)

    def test_missing_stats_file_returns_zero(self):
        sftp = _make_sftp()
        sftp.open.side_effect = FileNotFoundError
        sftp.listdir.side_effect = FileNotFoundError
        result = collect_player_data(sftp, 'test-uuid')
        self.assertEqual(result['play_time_ticks'], 0)
        self.assertEqual(result['pokemons_caught'], 0)
        self.assertEqual(result['cobbledollars'], 0)

    def test_missing_cobblemon_file_returns_zero(self):
        import json

        sftp = MagicMock()

        def fake_open(path):
            if path.endswith('/stats/test-uuid.json'):
                content = {'stats': {'minecraft:custom': {'minecraft:play_time': 100}}}
                mock_file = MagicMock()
                mock_file.read.return_value = json.dumps(content).encode()
                mock_file.__enter__ = lambda s: s
                mock_file.__exit__ = MagicMock(return_value=False)
                return mock_file
            raise FileNotFoundError(path)

        sftp.open.side_effect = fake_open
        sftp.listdir.side_effect = FileNotFoundError

        result = collect_player_data(sftp, 'test-uuid')
        self.assertEqual(result['pokemons_caught'], 0)
        self.assertEqual(result['pokedex_registered'], 0)
        self.assertEqual(result['battles_won'], 0)
        self.assertEqual(result['cobbletcg_cards'], 0)
        self.assertEqual(result['cobbledollars'], 0)

    def test_pokemon_count_from_directory(self):
        sftp = _make_sftp(pokemon_count=12)
        result = collect_player_data(sftp, 'test-uuid')
        self.assertEqual(result['pokemons_caught'], 12)


@override_settings(**SFTP_SETTINGS)
class RunCollectionTest(TestCase):

    @patch('apps.collector.services.collection_service.get_sftp_client')
    @patch('apps.collector.services.collection_service.collect_player_data')
    def test_creates_ok_log(self, mock_collect, mock_sftp_client):
        mock_sftp = MagicMock()
        mock_sftp.listdir.return_value = ['abc-123.json']
        mock_sftp.get_channel.return_value.get_transport.return_value = MagicMock()
        mock_sftp_client.return_value = mock_sftp
        mock_collect.return_value = {
            'play_time_ticks': 1000, 'pokemons_caught': 5,
            'pokedex_registered': 3, 'cobbletcg_cards': 2,
            'battles_won': 1, 'cobbledollars': 500,
        }

        from apps.collector.tasks import run_collection
        run_collection()

        log = CollectionLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, CollectionLog.STATUS_OK)
        self.assertEqual(log.players_updated, 1)

    @patch('apps.collector.services.collection_service.get_sftp_client', side_effect=Exception("connection refused"))
    def test_creates_error_log_on_failure(self, mock_sftp_client):
        from apps.collector.tasks import run_collection
        run_collection()

        log = CollectionLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, CollectionLog.STATUS_ERROR)
        self.assertIn("connection refused", log.message)

    def test_skips_collection_when_sftp_host_empty(self):
        with self.settings(SFTP_HOST=''):
            from apps.collector.tasks import run_collection
            run_collection()

        log = CollectionLog.objects.last()
        self.assertEqual(log.status, CollectionLog.STATUS_ERROR)
        self.assertIn("not configured", log.message)
