from django.db import IntegrityError
from django.test import TestCase, tag

from features.players.models import Player, PlayerStats
from features.players.repositories.player_repository import PlayerRepository
from features.players.repositories.stats_repository import PlayerStatsRepository


@tag("unit")
class PlayerModelTest(TestCase):
    def test_create_player(self):
        player = Player.objects.create(uuid="test-uuid-001", username="AshKetchum")
        self.assertEqual(str(player), "AshKetchum")
        self.assertEqual(player.pk, "test-uuid-001")
        self.assertIsNone(player.last_seen)

    def test_uuid_is_primary_key(self):
        Player.objects.create(uuid="uuid-a", username="PlayerA")
        Player.objects.create(uuid="uuid-b", username="PlayerB")
        self.assertEqual(Player.objects.count(), 2)
        with self.assertRaises(Exception):
            Player.objects.create(uuid="uuid-a", username="Duplicate")


@tag("unit")
class PlayerStatsModelTest(TestCase):
    def setUp(self):
        self.player = Player.objects.create(uuid="stats-uuid-001", username="Trainer")

    def test_default_values(self):
        stats = PlayerStats.objects.create(player=self.player)
        self.assertEqual(stats.play_time_ticks, 0)
        self.assertEqual(stats.pokemons_caught, 0)
        self.assertEqual(stats.pokedex_registered, 0)
        self.assertEqual(stats.cobbletcg_cards, 0)
        self.assertEqual(stats.battles_won, 0)
        self.assertEqual(stats.cobbledollars, 0)

    def test_one_to_one_constraint(self):
        PlayerStats.objects.create(player=self.player)
        with self.assertRaises(IntegrityError):
            PlayerStats.objects.create(player=self.player)

    def test_related_name(self):
        PlayerStats.objects.create(player=self.player, pokemons_caught=42)
        self.assertEqual(self.player.stats.pokemons_caught, 42)


@tag("unit")
class PlayerRepositoryTest(TestCase):
    def setUp(self):
        self.repo = PlayerRepository()

    def test_count_empty(self):
        self.assertEqual(self.repo.count(), 0)

    def test_count_with_players(self):
        Player.objects.create(uuid="uuid-1", username="Ash")
        Player.objects.create(uuid="uuid-2", username="Misty")
        self.assertEqual(self.repo.count(), 2)

    def test_get_or_create_creates_new_player(self):
        player, created = self.repo.get_or_create("uuid-new", "Brock")
        self.assertTrue(created)
        self.assertEqual(player.username, "Brock")
        self.assertEqual(player.uuid, "uuid-new")

    def test_get_or_create_returns_existing(self):
        Player.objects.create(uuid="uuid-x", username="Brock")
        player, created = self.repo.get_or_create("uuid-x", "Brock")
        self.assertFalse(created)
        self.assertEqual(Player.objects.count(), 1)

    def test_get_or_create_does_not_update_username(self):
        Player.objects.create(uuid="uuid-x", username="OldName")
        player, created = self.repo.get_or_create("uuid-x", "NewName")
        self.assertFalse(created)
        self.assertEqual(player.username, "OldName")

    def test_get_all_with_stats_returns_all(self):
        p1 = Player.objects.create(uuid="uuid-1", username="Ash")
        p2 = Player.objects.create(uuid="uuid-2", username="Misty")
        PlayerStats.objects.create(player=p1)
        PlayerStats.objects.create(player=p2)
        result = list(self.repo.get_all_with_stats())
        self.assertEqual(len(result), 2)

    def test_get_all_with_stats_ordered_by_username_by_default(self):
        p1 = Player.objects.create(uuid="uuid-1", username="Misty")
        p2 = Player.objects.create(uuid="uuid-2", username="Ash")
        PlayerStats.objects.create(player=p1)
        PlayerStats.objects.create(player=p2)
        result = list(self.repo.get_all_with_stats())
        self.assertEqual(result[0].username, "Ash")
        self.assertEqual(result[1].username, "Misty")

    def test_get_all_with_stats_with_sort(self):
        p1 = Player.objects.create(uuid="uuid-1", username="Ash")
        p2 = Player.objects.create(uuid="uuid-2", username="Misty")
        PlayerStats.objects.create(player=p1, pokemons_caught=10)
        PlayerStats.objects.create(player=p2, pokemons_caught=50)
        result = list(self.repo.get_all_with_stats(sort_field="pokemons_caught"))
        self.assertEqual(result[0].username, "Misty")


@tag("unit")
class PlayerStatsRepositoryTest(TestCase):
    def setUp(self):
        self.repo = PlayerStatsRepository()
        p1 = Player.objects.create(uuid="uuid-1", username="Ash")
        p2 = Player.objects.create(uuid="uuid-2", username="Misty")
        p3 = Player.objects.create(uuid="uuid-3", username="Brock")
        PlayerStats.objects.create(player=p1, play_time_ticks=300, pokemons_caught=100)
        PlayerStats.objects.create(player=p2, play_time_ticks=200, pokemons_caught=50)
        PlayerStats.objects.create(player=p3, play_time_ticks=100, pokemons_caught=25)

    def test_get_leader_by_field_returns_top(self):
        leader = self.repo.get_leader_by_field("play_time_ticks")
        self.assertEqual(leader.player.username, "Ash")

    def test_get_leader_by_field_empty_db(self):
        PlayerStats.objects.all().delete()
        self.assertIsNone(self.repo.get_leader_by_field("play_time_ticks"))

    def test_get_top_by_field_returns_ordered(self):
        result = self.repo.get_top_by_field("play_time_ticks")
        self.assertEqual(result[0].player.username, "Ash")
        self.assertEqual(result[1].player.username, "Misty")
        self.assertEqual(result[2].player.username, "Brock")

    def test_get_top_by_field_respects_n(self):
        result = self.repo.get_top_by_field("play_time_ticks", n=2)
        self.assertEqual(len(result), 2)

    def test_get_top_by_field_less_than_n(self):
        result = self.repo.get_top_by_field("play_time_ticks", n=10)
        self.assertEqual(len(result), 3)

    def test_get_last_updated_returns_most_recent(self):
        self.assertIsNotNone(self.repo.get_last_updated())

    def test_get_last_updated_empty_db(self):
        PlayerStats.objects.all().delete()
        self.assertIsNone(self.repo.get_last_updated())

    def test_update_or_create_creates(self):
        player = Player.objects.create(uuid="uuid-new", username="Gary")
        stats = self.repo.update_or_create(player, {"pokemons_caught": 99})
        self.assertEqual(stats.pokemons_caught, 99)

    def test_update_or_create_updates(self):
        player = Player.objects.get(uuid="uuid-1")
        self.repo.update_or_create(player, {"pokemons_caught": 999})
        player.stats.refresh_from_db()
        self.assertEqual(player.stats.pokemons_caught, 999)
