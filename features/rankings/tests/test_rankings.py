from django.test import TestCase, tag
from django.urls import reverse

from features.players.models import Player, PlayerStats
from features.players.repositories.stats_repository import PlayerStatsRepository
from features.rankings.config import RANKINGS
from features.rankings.formatters import format_value
from features.rankings.services.ranking_service import RankingService


@tag("unit")
class FormatValueTest(TestCase):
    def test_hours_converts_ticks(self):
        # 72000 ticks = 1 hour (72000 / 20 / 3600)
        self.assertEqual(format_value(72000, "hours"), "1h")

    def test_hours_zero(self):
        self.assertEqual(format_value(0, "hours"), "0h")

    def test_hours_large(self):
        # 720000 ticks = 10 hours
        self.assertEqual(format_value(720000, "hours"), "10h")

    def test_number_plain(self):
        self.assertEqual(format_value(150, "number"), "150")

    def test_number_with_comma(self):
        self.assertEqual(format_value(1000, "number"), "1,000")

    def test_currency_format(self):
        self.assertEqual(format_value(5000, "currency"), "₡ 5,000")

    def test_currency_zero(self):
        self.assertEqual(format_value(0, "currency"), "₡ 0")

    def test_unknown_format_falls_back_to_number(self):
        self.assertEqual(format_value(1000, "unknown"), "1,000")


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("integration")
class RankingsViewTest(TestCase):
    def setUp(self):
        _make_player(
            "uuid-1",
            "AshKetchum",
            play_time_ticks=72000,
            pokemons_caught=100,
            pokedex_registered=50,
            cobbletcg_cards=20,
            battles_won=30,
            cobbledollars=5000,
        )
        _make_player(
            "uuid-2",
            "MistyWater",
            play_time_ticks=36000,
            pokemons_caught=80,
            pokedex_registered=40,
            cobbletcg_cards=15,
            battles_won=20,
            cobbledollars=3000,
        )
        _make_player(
            "uuid-3",
            "BrockRock",
            play_time_ticks=14400,
            pokemons_caught=60,
            pokedex_registered=30,
            cobbletcg_cards=10,
            battles_won=10,
            cobbledollars=1000,
        )

    def test_rankings_returns_200(self):
        resp = self.client.get(reverse("rankings:rankings"))
        self.assertEqual(resp.status_code, 200)

    def test_rankings_context_contains_all_ids(self):
        resp = self.client.get(reverse("rankings:rankings"))
        context_ids = [r["id"] for r in resp.context["rankings"]]
        expected_ids = [r["id"] for r in RANKINGS]
        self.assertEqual(context_ids, expected_ids)

    def test_hours_ranking_ordered_descending(self):
        resp = self.client.get(reverse("rankings:rankings"))
        hours_ranking = next(r for r in resp.context["rankings"] if r["id"] == "hours")
        names = [p["name"] for p in hours_ranking["players"]]
        self.assertEqual(names[0], "AshKetchum")
        self.assertEqual(names[1], "MistyWater")
        self.assertEqual(names[2], "BrockRock")

    def test_money_ranking_ordered_descending(self):
        resp = self.client.get(reverse("rankings:rankings"))
        money_ranking = next(r for r in resp.context["rankings"] if r["id"] == "money")
        self.assertEqual(money_ranking["players"][0]["name"], "AshKetchum")

    def test_last_updated_in_context(self):
        resp = self.client.get(reverse("rankings:rankings"))
        self.assertIn("last_updated", resp.context)

    def test_bar_pct_first_player_is_100(self):
        resp = self.client.get(reverse("rankings:rankings"))
        hours_ranking = next(r for r in resp.context["rankings"] if r["id"] == "hours")
        self.assertEqual(hours_ranking["players"][0]["bar_pct"], 100)

    def test_formatted_value_in_players(self):
        resp = self.client.get(reverse("rankings:rankings"))
        hours_ranking = next(r for r in resp.context["rankings"] if r["id"] == "hours")
        # 72000 ticks = 1h
        self.assertEqual(hours_ranking["players"][0]["value"], "1h")

    def test_rankings_uses_correct_template(self):
        resp = self.client.get(reverse("rankings:rankings"))
        self.assertTemplateUsed(resp, "rankings/page.html")

    def test_rankings_players_have_expected_keys(self):
        resp = self.client.get(reverse("rankings:rankings"))
        hours_ranking = next(r for r in resp.context["rankings"] if r["id"] == "hours")
        player = hours_ranking["players"][0]
        self.assertIn("name", player)
        self.assertIn("value", player)
        self.assertIn("bar_pct", player)
        self.assertIn("raw_value", player)


@tag("unit")
class RankingServiceTest(TestCase):
    def setUp(self):
        self.service = RankingService(PlayerStatsRepository())
        _make_player(
            "uuid-1",
            "Ash",
            play_time_ticks=300,
            pokemons_caught=100,
            pokedex_registered=50,
            cobbletcg_cards=20,
            battles_won=30,
            cobbledollars=5000,
        )
        _make_player(
            "uuid-2",
            "Misty",
            play_time_ticks=200,
            pokemons_caught=80,
            pokedex_registered=40,
            cobbletcg_cards=15,
            battles_won=20,
            cobbledollars=3000,
        )
        _make_player(
            "uuid-3",
            "Brock",
            play_time_ticks=100,
            pokemons_caught=60,
            pokedex_registered=30,
            cobbletcg_cards=10,
            battles_won=10,
            cobbledollars=1000,
        )

    def test_get_home_leaders_returns_one_per_category(self):
        leaders = self.service.get_home_leaders()
        self.assertEqual(len(leaders), len(RANKINGS))

    def test_get_home_leaders_correct_leader(self):
        leaders = {entry["id"]: entry for entry in self.service.get_home_leaders()}
        self.assertEqual(leaders["hours"]["player_name"], "Ash")
        self.assertEqual(leaders["catches"]["player_name"], "Ash")

    def test_get_home_leaders_empty_db(self):
        PlayerStats.objects.all().delete()
        self.assertEqual(self.service.get_home_leaders(), [])

    def test_get_home_leaders_skips_category_with_no_leaders(self):
        PlayerStats.objects.all().delete()
        leaders = self.service.get_home_leaders()
        self.assertEqual(leaders, [])

    def test_get_full_rankings_returns_all_categories(self):
        rankings, _ = self.service.get_full_rankings()
        ids = [r["id"] for r in rankings]
        self.assertEqual(ids, [r["id"] for r in RANKINGS])

    def test_get_full_rankings_ordered_descending(self):
        rankings, _ = self.service.get_full_rankings()
        hours = next(r for r in rankings if r["id"] == "hours")
        values = [p["raw_value"] for p in hours["players"]]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_get_full_rankings_bar_pct_first_is_100(self):
        rankings, _ = self.service.get_full_rankings()
        for ranking in rankings:
            if ranking["players"]:
                self.assertEqual(ranking["players"][0]["bar_pct"], 100)

    def test_get_full_rankings_less_than_10_players(self):
        rankings, _ = self.service.get_full_rankings()
        hours = next(r for r in rankings if r["id"] == "hours")
        self.assertEqual(len(hours["players"]), 3)

    def test_get_full_rankings_last_updated_not_none(self):
        _, last_updated = self.service.get_full_rankings()
        self.assertIsNotNone(last_updated)

    def test_get_full_rankings_last_updated_none_when_empty(self):
        PlayerStats.objects.all().delete()
        _, last_updated = self.service.get_full_rankings()
        self.assertIsNone(last_updated)
