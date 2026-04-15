"""
Integration tests — verify that all public-facing views return the expected
status codes and that key template rendering works end-to-end.
"""
import datetime

from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from apps.players.models import Player, PlayerStats
from apps.rankings.config import RANKINGS
from apps.wiki.models import WikiPage


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


class PublicViewsTest(TestCase):

    def setUp(self):
        _make_player(
            'int-uuid-1', 'AshKetchum',
            play_time_ticks=72000, pokemons_caught=100,
            pokedex_registered=50, cobbletcg_cards=20,
            battles_won=30, cobbledollars=5000,
        )
        WikiPage.objects.create(slug='guide', title='Guide', content='# Hello\n\nWelcome.')

    def test_home_returns_200(self):
        resp = self.client.get(reverse('rankings:home'))
        self.assertEqual(resp.status_code, 200)

    def test_rankings_returns_200(self):
        resp = self.client.get(reverse('rankings:rankings'))
        self.assertEqual(resp.status_code, 200)

    def test_rankings_has_all_six_sections(self):
        resp = self.client.get(reverse('rankings:rankings'))
        self.assertEqual(len(resp.context['rankings']), len(RANKINGS))
        self.assertEqual(len(resp.context['rankings']), 6)

    def test_wiki_list_returns_200(self):
        resp = self.client.get(reverse('wiki:wiki-list'))
        self.assertEqual(resp.status_code, 200)

    def test_wiki_detail_renders_html(self):
        resp = self.client.get(reverse('wiki:wiki-detail', args=['guide']))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<h1>', resp.context['content_html'])

    def test_health_check_returns_200(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)


class DiscordCardTemplateTest(TestCase):
    """The discord card template must render without errors (used by Playwright)."""

    def setUp(self):
        self.player = _make_player(
            'int-uuid-dc', 'TracySketch',
            play_time_ticks=144000, pokemons_caught=200,
            pokedex_registered=100, cobbletcg_cards=40,
            battles_won=60, cobbledollars=10000,
        )

    def test_discord_card_template_renders(self):
        ranking = RANKINGS[0]
        players = [
            {'rank': 1, 'name': 'TracySketch', 'value': '2h', 'bar_pct': 100},
        ]
        html = render_to_string('rankings/discord_card.html', {
            'ranking': ranking,
            'players': players,
            'date': datetime.date.today().strftime('%d %b %Y'),
        })
        self.assertIn('TracySketch', html)
        self.assertIn(ranking['label'].upper(), html)

    def test_discord_card_template_has_all_rankings(self):
        for ranking in RANKINGS:
            html = render_to_string('rankings/discord_card.html', {
                'ranking': ranking,
                'players': [],
                'date': '01 Jan 2026',
            })
            self.assertIn(ranking['label'].upper(), html)


class DashboardAccessTest(TestCase):

    def test_dashboard_home_redirects_anonymous(self):
        resp = self.client.get(reverse('dashboard:home'))
        self.assertIn(resp.status_code, (301, 302))

    def test_dashboard_players_redirects_anonymous(self):
        resp = self.client.get(reverse('dashboard:players'))
        self.assertIn(resp.status_code, (301, 302))

    def test_dashboard_accessible_by_staff(self):
        staff = User.objects.create_user('admin', password='pass', is_staff=True)
        self.client.force_login(staff)
        resp = self.client.get(reverse('dashboard:home'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_wiki_list_accessible_by_staff(self):
        staff = User.objects.create_user('admin2', password='pass', is_staff=True)
        self.client.force_login(staff)
        resp = self.client.get(reverse('dashboard:wiki-list'))
        self.assertEqual(resp.status_code, 200)
