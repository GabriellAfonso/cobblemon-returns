import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings, tag

from features.collector.models import CollectionLog
from features.collector.repositories.log_repository import CollectionLogRepository
from features.collector.sftp import collect_player_data, read_json_file, read_usercache

SFTP_SETTINGS = {
    "SFTP_HOST": "sftp.example.com",
    "SFTP_PORT": "22",
    "SFTP_USER": "user",
    "SFTP_KEY_PATH": "/tmp/key",
    "MINECRAFT_WORLD_PATH": "/world",
    "COBBLEMON_DATA_PATH": "/cobblemon",
    "COBBLE_ECONOMY_PATH": "/economy",
    "COBBLE_TCG_PATH": "/tcg",
    "COLLECTOR_INTERVAL_MINUTES": 15,
}


def _make_sftp(
    stats_json=None,
    cobblemon_json=None,
    economy_json=None,
    pokemon_count=5,
    tcg_count=3,
):
    """Build a MagicMock SFTP client with configurable file responses."""
    import json

    sftp = MagicMock()

    def fake_open(path):
        if path.endswith("/stats/test-uuid.json"):
            content = stats_json or {
                "stats": {"minecraft:custom": {"minecraft:play_time": 72000}}
            }
        elif path.endswith("/data.json"):
            content = cobblemon_json or {"caughtPokemon": 150, "battleWins": 42}
        elif path.endswith(".json"):
            content = economy_json or {"balance": 1000}
        else:
            raise FileNotFoundError(path)

        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(content).encode()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        return mock_file

    sftp.open.side_effect = fake_open
    sftp.listdir.side_effect = lambda path: (
        [f"{i}.json" for i in range(pokemon_count)]
        if "pokemon" in path
        else [f"card{i}.json" for i in range(tcg_count)]
    )
    return sftp


@tag("unit")
@override_settings(**SFTP_SETTINGS)
class CollectPlayerDataTest(TestCase):
    def test_returns_all_stat_keys(self):
        sftp = _make_sftp()
        result = collect_player_data(sftp, "test-uuid")
        expected_keys = {
            "play_time_ticks",
            "pokemons_caught",
            "pokedex_registered",
            "cobbletcg_cards",
            "battles_won",
            "cobbledollars",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_reads_play_time(self):
        sftp = _make_sftp(
            stats_json={"stats": {"minecraft:custom": {"minecraft:play_time": 36000}}}
        )
        result = collect_player_data(sftp, "test-uuid")
        self.assertEqual(result["play_time_ticks"], 36000)

    def test_missing_stats_file_returns_zero(self):
        sftp = _make_sftp()
        sftp.open.side_effect = FileNotFoundError
        sftp.listdir.side_effect = FileNotFoundError
        result = collect_player_data(sftp, "test-uuid")
        self.assertEqual(result["play_time_ticks"], 0)
        self.assertEqual(result["pokemons_caught"], 0)
        self.assertEqual(result["cobbledollars"], 0)

    def test_missing_cobblemon_file_returns_zero(self):
        import json

        sftp = MagicMock()

        def fake_open(path):
            if path.endswith("/stats/test-uuid.json"):
                content = {"stats": {"minecraft:custom": {"minecraft:play_time": 100}}}
                mock_file = MagicMock()
                mock_file.read.return_value = json.dumps(content).encode()
                mock_file.__enter__ = lambda s: s
                mock_file.__exit__ = MagicMock(return_value=False)
                return mock_file
            raise FileNotFoundError(path)

        sftp.open.side_effect = fake_open
        sftp.listdir.side_effect = FileNotFoundError

        result = collect_player_data(sftp, "test-uuid")
        self.assertEqual(result["pokemons_caught"], 0)
        self.assertEqual(result["pokedex_registered"], 0)
        self.assertEqual(result["battles_won"], 0)
        self.assertEqual(result["cobbletcg_cards"], 0)
        self.assertEqual(result["cobbledollars"], 0)

    def test_pokemon_count_from_directory(self):
        sftp = _make_sftp(pokemon_count=12)
        result = collect_player_data(sftp, "test-uuid")
        self.assertEqual(result["pokemons_caught"], 12)


@tag("integration")
@override_settings(**SFTP_SETTINGS)
class RunCollectionTest(TestCase):
    @patch("features.collector.services.collection_service.get_sftp_client")
    @patch("features.collector.services.collection_service.collect_player_data")
    def test_creates_ok_log(self, mock_collect, mock_sftp_client):
        mock_sftp = MagicMock()
        mock_sftp.listdir.return_value = ["abc-123.json"]
        mock_sftp.get_channel.return_value.get_transport.return_value = MagicMock()
        mock_sftp_client.return_value = mock_sftp
        mock_collect.return_value = {
            "play_time_ticks": 1000,
            "pokemons_caught": 5,
            "pokedex_registered": 3,
            "cobbletcg_cards": 2,
            "battles_won": 1,
            "cobbledollars": 500,
        }

        from features.collector.tasks import run_collection

        run_collection()

        log = CollectionLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, CollectionLog.STATUS_OK)
        self.assertEqual(log.players_updated, 1)

    @patch(
        "features.collector.services.collection_service.get_sftp_client",
        side_effect=Exception("connection refused"),
    )
    def test_creates_error_log_on_failure(self, mock_sftp_client):
        from features.collector.tasks import run_collection

        run_collection()

        log = CollectionLog.objects.last()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, CollectionLog.STATUS_ERROR)
        self.assertIn("connection refused", log.message)

    def test_skips_collection_when_sftp_host_empty(self):
        with self.settings(SFTP_HOST=""):
            from features.collector.tasks import run_collection

            run_collection()

        log = CollectionLog.objects.last()
        self.assertEqual(log.status, CollectionLog.STATUS_ERROR)
        self.assertIn("not configured", log.message)


@tag("unit")
class CollectionLogModelTest(TestCase):
    def test_str_representation(self):
        log = CollectionLog.objects.create(status="ok", players_updated=5)
        self.assertIn("OK", str(log))
        self.assertIn("5 players", str(log))

    def test_timestamp_is_set_on_create(self):
        log = CollectionLog.objects.create(status="ok")
        self.assertIsNotNone(log.timestamp)

    def test_default_players_updated_is_zero(self):
        log = CollectionLog.objects.create(status="ok")
        self.assertEqual(log.players_updated, 0)

    def test_ordering_newest_first(self):
        CollectionLog.objects.create(status="ok", players_updated=1)
        CollectionLog.objects.create(status="error", players_updated=2)
        logs = list(CollectionLog.objects.all())
        self.assertEqual(logs[0].players_updated, 2)
        self.assertEqual(logs[1].players_updated, 1)


@tag("unit")
class CollectionLogRepositoryTest(TestCase):
    def setUp(self):
        self.repo = CollectionLogRepository()

    def test_create_log(self):
        log = self.repo.create(status="ok", message="done", players_updated=3)
        self.assertEqual(log.status, "ok")
        self.assertEqual(log.message, "done")
        self.assertEqual(log.players_updated, 3)

    def test_get_latest_returns_most_recent(self):
        self.repo.create(status="ok", players_updated=1)
        self.repo.create(status="error", players_updated=2)
        latest = self.repo.get_latest()
        self.assertEqual(latest.players_updated, 2)

    def test_get_latest_returns_none_when_empty(self):
        self.assertIsNone(self.repo.get_latest())

    def test_get_last_n_limits_results(self):
        for i in range(10):
            self.repo.create(status="ok", players_updated=i)
        result = list(self.repo.get_last_n(5))
        self.assertEqual(len(result), 5)


@tag("unit")
@override_settings(**SFTP_SETTINGS)
class SftpHelpersTest(TestCase):
    def _make_sftp_with_file(self, content: dict) -> MagicMock:
        sftp = MagicMock()
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(content).encode()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        sftp.open.return_value = mock_file
        return sftp

    def test_read_json_file_returns_parsed_dict(self):
        sftp = self._make_sftp_with_file({"key": "value"})
        result = read_json_file(sftp, "/some/path.json")
        self.assertEqual(result, {"key": "value"})

    def test_read_json_file_returns_none_on_error(self):
        sftp = MagicMock()
        sftp.open.side_effect = FileNotFoundError
        result = read_json_file(sftp, "/missing.json")
        self.assertIsNone(result)

    def test_read_usercache_returns_uuid_name_map(self):
        cache = [
            {"uuid": "uuid-1", "name": "Ash"},
            {"uuid": "uuid-2", "name": "Misty"},
        ]
        sftp = self._make_sftp_with_file(cache)
        result = read_usercache(sftp)
        self.assertEqual(result["uuid-1"], "Ash")
        self.assertEqual(result["uuid-2"], "Misty")

    def test_read_usercache_returns_empty_on_missing_file(self):
        sftp = MagicMock()
        sftp.open.side_effect = FileNotFoundError
        result = read_usercache(sftp)
        self.assertEqual(result, {})

    def test_read_usercache_skips_entries_without_uuid_or_name(self):
        cache = [
            {"uuid": "uuid-1", "name": "Ash"},
            {"name": "NoUUID"},
            {"uuid": "uuid-3"},
        ]
        sftp = self._make_sftp_with_file(cache)
        result = read_usercache(sftp)
        self.assertEqual(len(result), 1)
        self.assertIn("uuid-1", result)
