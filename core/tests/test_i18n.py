from django.test import TestCase, tag
from django.urls import reverse
from django.utils import translation

from features.players.models import Player, PlayerStats
from features.rankings.config import RANKINGS


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("integration")
class LanguageSwitchEndpointTest(TestCase):
    def test_set_language_redirects(self):
        resp = self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": "/"},
        )
        self.assertIn(resp.status_code, [301, 302])

    def test_set_language_sets_cookie(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": "/"},
        )
        self.assertIn("django_language", self.client.cookies)
        self.assertEqual(self.client.cookies["django_language"].value, "pt-br")

    def test_set_language_to_english_sets_cookie(self):
        self.client.post(
            reverse("set_language"),
            {"language": "en", "next": "/"},
        )
        self.assertEqual(self.client.cookies["django_language"].value, "en")


@tag("integration")
class HomePageI18nTest(TestCase):
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

    def test_home_default_language_is_english(self):
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, "Install Modpack")
        self.assertContains(resp, "View Rankings")
        self.assertContains(resp, "Current Leaders")

    def test_home_portuguese_via_accept_language(self):
        resp = self.client.get(
            reverse("home:home"),
            HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9",
        )
        self.assertContains(resp, "Instalar Modpack")
        self.assertContains(resp, "Ver Rankings")
        self.assertContains(resp, "Líderes Atuais")

    def test_home_portuguese_after_language_switch(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": "/"},
        )
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, "Instalar Modpack")
        self.assertContains(resp, "Ver Rankings")

    def test_home_english_after_language_switch(self):
        self.client.post(
            reverse("set_language"),
            {"language": "en", "next": "/"},
        )
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, "Install Modpack")
        self.assertNotContains(resp, "Instalar Modpack")

    def test_html_lang_attribute_english(self):
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, 'lang="en"')

    def test_html_lang_attribute_portuguese(self):
        resp = self.client.get(
            reverse("home:home"),
            HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9",
        )
        self.assertContains(resp, 'lang="pt-br"')

    def test_language_switcher_buttons_present(self):
        resp = self.client.get(reverse("home:home"))
        self.assertContains(resp, 'name="language" value="en"')
        self.assertContains(resp, 'name="language" value="pt-br"')

    def test_en_button_active_on_english(self):
        resp = self.client.get(reverse("home:home"))
        content = resp.content.decode()
        en_btn_idx = content.find('value="en"')
        snippet = content[en_btn_idx : en_btn_idx + 60]
        self.assertIn("active", snippet)

    def test_pt_button_active_on_portuguese(self):
        self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": "/"},
        )
        resp = self.client.get(reverse("home:home"))
        content = resp.content.decode()
        pt_btn_idx = content.find('value="pt-br"')
        snippet = content[pt_btn_idx : pt_btn_idx + 60]
        self.assertIn("active", snippet)

    def test_js_status_strings_translated_to_portuguese(self):
        resp = self.client.get(
            reverse("home:home"),
            HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9",
        )
        self.assertContains(resp, "Carregando...")
        self.assertContains(resp, "STATUS_ONLINE = 'Online'")
        self.assertContains(resp, "STATUS_OFFLINE = 'Offline'")


@tag("unit")
class RankingsConfigTranslationTest(TestCase):
    def test_labels_in_english_by_default(self):
        with translation.override("en"):
            labels = [str(r["label"]) for r in RANKINGS]
        self.assertIn("Hours Played", labels)
        self.assertIn("Battles Won", labels)

    def test_labels_translated_to_portuguese(self):
        with translation.override("pt-br"):
            labels = [str(r["label"]) for r in RANKINGS]
        self.assertIn("Horas Jogadas", labels)
        self.assertIn("Batalhas Vencidas", labels)
        self.assertIn("Pokémons Capturados", labels)


@tag("integration")
class RankingsPageI18nTest(TestCase):
    def test_rankings_english(self):
        resp = self.client.get(reverse("rankings:rankings"))
        self.assertContains(resp, "Hall of Fame")
        self.assertContains(resp, "Hours Played")

    def test_rankings_portuguese(self):
        resp = self.client.get(
            reverse("rankings:rankings"),
            HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9",
        )
        self.assertContains(resp, "Hall da Fama")
        self.assertContains(resp, "Horas Jogadas")


@tag("integration")
class WikiPageI18nTest(TestCase):
    def test_wiki_list_english(self):
        resp = self.client.get(reverse("wiki:wiki-list"))
        self.assertContains(resp, "Knowledge Base")

    def test_wiki_list_portuguese(self):
        resp = self.client.get(
            reverse("wiki:wiki-list"),
            HTTP_ACCEPT_LANGUAGE="pt-BR,pt;q=0.9",
        )
        self.assertContains(resp, "Base de Conhecimento")
        self.assertContains(resp, "Nenhuma página na wiki ainda.")
