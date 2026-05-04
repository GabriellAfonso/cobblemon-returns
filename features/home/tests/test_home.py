from django.test import TestCase, tag
from django.urls import resolve, reverse

from features.players.models import Player, PlayerStats
from features.rankings.config import RANKINGS


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("integration")
class HomeViewTest(TestCase):
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

    def test_home_returns_200(self):
        resp = self.client.get(reverse("home:home"))
        self.assertEqual(resp.status_code, 200)

    def test_home_uses_correct_template(self):
        resp = self.client.get(reverse("home:home"))
        self.assertTemplateUsed(resp, "home/home.html")

    def test_home_url_resolves_to_root(self):
        self.assertEqual(reverse("home:home"), "/")

    def test_home_url_resolves_to_home_view(self):
        from features.home.views import HomeView

        match = resolve("/")
        self.assertEqual(match.func.view_class, HomeView)

    def test_home_has_leaders(self):
        resp = self.client.get(reverse("home:home"))
        self.assertIn("leaders", resp.context)
        self.assertEqual(len(resp.context["leaders"]), len(RANKINGS))

    def test_leaders_have_expected_keys(self):
        resp = self.client.get(reverse("home:home"))
        for leader in resp.context["leaders"]:
            self.assertIn("icon", leader)
            self.assertIn("label", leader)
            self.assertIn("player_name", leader)
            self.assertIn("value", leader)

    def test_top_player_is_correct_per_category(self):
        _make_player(
            "uuid-2",
            "MistyWater",
            play_time_ticks=36000,
            pokemons_caught=200,
            pokedex_registered=10,
            cobbletcg_cards=5,
            battles_won=5,
            cobbledollars=1000,
        )
        resp = self.client.get(reverse("home:home"))
        leaders = {entry["id"]: entry for entry in resp.context["leaders"]}
        self.assertEqual(leaders["hours"]["player_name"], "AshKetchum")
        self.assertEqual(leaders["catches"]["player_name"], "MistyWater")

    def test_home_empty_leaders_when_no_data(self):
        PlayerStats.objects.all().delete()
        Player.objects.all().delete()
        resp = self.client.get(reverse("home:home"))
        self.assertEqual(resp.context["leaders"], [])
