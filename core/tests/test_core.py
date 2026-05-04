from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, tag
from django.urls import reverse

from features.players.models import Player, PlayerStats


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("unit")
class BaseTemplateTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _render_base(self) -> str:
        request = self.factory.get("/")
        return render_to_string("core/base.html", request=request)

    def test_base_template_renders_without_error(self):
        html = self._render_base()
        self.assertIn("<!DOCTYPE html>", html)

    def test_base_has_nav(self):
        html = self._render_base()
        self.assertIn("<nav>", html)

    def test_base_nav_has_home_link(self):
        html = self._render_base()
        self.assertIn(reverse("home:home"), html)

    def test_base_nav_has_rankings_link(self):
        html = self._render_base()
        self.assertIn(reverse("rankings:rankings"), html)

    def test_base_nav_has_wiki_link(self):
        html = self._render_base()
        self.assertIn(reverse("wiki:wiki-list"), html)

    def test_base_has_footer(self):
        html = self._render_base()
        self.assertIn("<footer>", html)

    def test_base_loads_base_css(self):
        html = self._render_base()
        self.assertIn("core/css/base.css", html)

    def test_base_loads_favicon(self):
        html = self._render_base()
        self.assertIn("core/images/favicon.ico", html)


@tag("integration")
class NavActiveStateTest(TestCase):
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

    def test_home_link_is_active_on_home_page(self):
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, 'href="/" class="active"')

    def test_rankings_link_is_active_on_rankings_page(self):
        resp = self.client.get(reverse("rankings:rankings"))
        self.assertContains(resp, 'class="active"')
        content = resp.content.decode()
        rankings_url = reverse("rankings:rankings")
        active_idx = content.find('class="active"')
        link_idx = content.rfind(rankings_url, 0, active_idx)
        self.assertGreater(link_idx, -1)

    def test_home_link_not_active_on_rankings_page(self):
        resp = self.client.get(reverse("rankings:rankings"))
        content = resp.content.decode()
        home_url = reverse("home:home")
        home_link_idx = content.find(f'href="{home_url}"')
        snippet = content[home_link_idx : home_link_idx + 60]
        self.assertNotIn("active", snippet)
