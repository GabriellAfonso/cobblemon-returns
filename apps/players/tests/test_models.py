from django.db import IntegrityError
from django.test import TestCase

from apps.players.models import Player, PlayerStats


class PlayerModelTest(TestCase):

    def test_create_player(self):
        player = Player.objects.create(uuid='test-uuid-001', username='AshKetchum')
        self.assertEqual(str(player), 'AshKetchum')
        self.assertEqual(player.pk, 'test-uuid-001')
        self.assertIsNone(player.last_seen)

    def test_uuid_is_primary_key(self):
        Player.objects.create(uuid='uuid-a', username='PlayerA')
        Player.objects.create(uuid='uuid-b', username='PlayerB')
        self.assertEqual(Player.objects.count(), 2)
        with self.assertRaises(Exception):
            Player.objects.create(uuid='uuid-a', username='Duplicate')


class PlayerStatsModelTest(TestCase):

    def setUp(self):
        self.player = Player.objects.create(uuid='stats-uuid-001', username='Trainer')

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
        stats = PlayerStats.objects.create(player=self.player, pokemons_caught=42)
        self.assertEqual(self.player.stats.pokemons_caught, 42)
