from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse

from features.collector.models import CollectionLog
from features.collector.repositories.log_repository import CollectionLogRepository
from features.dashboard.services.dashboard_service import DashboardService
from features.players.models import Player, PlayerStats
from features.players.repositories.player_repository import PlayerRepository
from features.wiki.models import WikiPage

User = get_user_model()


def _staff_user():
    return User.objects.create_user(username="staff", password="pass", is_staff=True)


def _regular_user():
    return User.objects.create_user(username="regular", password="pass", is_staff=False)


def _make_player(uuid, username, **stats):
    p = Player.objects.create(uuid=uuid, username=username)
    PlayerStats.objects.create(player=p, **stats)
    return p


@tag("integration")
class StaffRequiredTest(TestCase):
    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp["Location"])

    def test_non_staff_gets_403(self):
        _regular_user()
        self.client.login(username="regular", password="pass")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 403)

    def test_staff_can_access(self):
        _staff_user()
        self.client.login(username="staff", password="pass")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)


@tag("integration")
class WikiCreateViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")

    def test_create_wiki_page(self):
        self.client.post(
            reverse("dashboard:wiki-create"),
            {
                "title": "New Page",
                "slug": "new-page",
                "content": "# Hello\nContent here.",
            },
        )
        self.assertEqual(WikiPage.objects.filter(slug="new-page").count(), 1)

    def test_create_redirects_to_list(self):
        resp = self.client.post(
            reverse("dashboard:wiki-create"),
            {
                "title": "Redirect Test",
                "slug": "redirect-test",
                "content": "Some content.",
            },
        )
        self.assertRedirects(resp, reverse("dashboard:wiki-list"))

    def test_create_get_returns_200(self):
        resp = self.client.get(reverse("dashboard:wiki-create"))
        self.assertEqual(resp.status_code, 200)


@tag("integration")
class WikiDeleteViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")
        self.page = WikiPage.objects.create(
            slug="to-delete", title="To Delete", content="bye"
        )

    def test_delete_removes_page(self):
        self.client.post(reverse("dashboard:wiki-delete", args=["to-delete"]))
        self.assertFalse(WikiPage.objects.filter(slug="to-delete").exists())

    def test_delete_get_shows_confirmation(self):
        resp = self.client.get(reverse("dashboard:wiki-delete", args=["to-delete"]))
        self.assertEqual(resp.status_code, 200)

    def test_delete_redirects_to_list(self):
        resp = self.client.post(reverse("dashboard:wiki-delete", args=["to-delete"]))
        self.assertRedirects(resp, reverse("dashboard:wiki-list"))


@tag("integration")
class CollectionLogViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")
        for i in range(60):
            CollectionLog.objects.create(status="ok", players_updated=i)

    def test_log_view_returns_200(self):
        resp = self.client.get(reverse("dashboard:logs"))
        self.assertEqual(resp.status_code, 200)

    def test_log_view_returns_at_most_50(self):
        resp = self.client.get(reverse("dashboard:logs"))
        self.assertLessEqual(len(resp.context["logs"]), 50)


@tag("unit")
class DashboardServiceTest(TestCase):
    def setUp(self):
        self.service = DashboardService(PlayerRepository(), CollectionLogRepository())

    def test_get_summary_returns_total_players(self):
        _make_player("uuid-1", "Ash")
        _make_player("uuid-2", "Misty")
        summary = self.service.get_summary()
        self.assertEqual(summary["total_players"], 2)

    def test_get_summary_returns_last_log(self):
        log = CollectionLog.objects.create(status="ok", players_updated=5)
        summary = self.service.get_summary()
        self.assertEqual(summary["last_log"], log)

    def test_get_summary_last_log_none_when_empty(self):
        summary = self.service.get_summary()
        self.assertIsNone(summary["last_log"])

    def test_get_players_without_sort(self):
        _make_player("uuid-1", "Misty")
        _make_player("uuid-2", "Ash")
        result = list(self.service.get_players())
        self.assertEqual(result[0].username, "Ash")

    def test_get_players_with_sort(self):
        _make_player("uuid-1", "Ash", pokemons_caught=10)
        _make_player("uuid-2", "Misty", pokemons_caught=50)
        result = list(self.service.get_players("pokemons_caught"))
        self.assertEqual(result[0].username, "Misty")

    def test_get_logs_returns_at_most_n(self):
        for i in range(10):
            CollectionLog.objects.create(status="ok", players_updated=i)
        result = list(self.service.get_logs(5))
        self.assertEqual(len(result), 5)


@tag("integration")
class DashboardHomeViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")

    def test_context_has_total_players(self):
        _make_player("uuid-1", "Ash")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertIn("total_players", resp.context)
        self.assertEqual(resp.context["total_players"], 1)

    def test_context_has_last_log(self):
        CollectionLog.objects.create(status="ok", players_updated=3)
        resp = self.client.get(reverse("dashboard:home"))
        self.assertIn("last_log", resp.context)
        self.assertIsNotNone(resp.context["last_log"])

    def test_context_has_next_run_key(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertIn("next_run", resp.context)


@tag("integration")
class PlayersListViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")
        _make_player("uuid-1", "Ash", pokemons_caught=10)
        _make_player("uuid-2", "Misty", pokemons_caught=50)

    def test_players_list_returns_200(self):
        resp = self.client.get(reverse("dashboard:players"))
        self.assertEqual(resp.status_code, 200)

    def test_valid_sort_param_is_applied(self):
        resp = self.client.get(reverse("dashboard:players") + "?sort=pokemons_caught")
        players = list(resp.context["players"])
        self.assertEqual(players[0].username, "Misty")

    def test_invalid_sort_param_is_ignored(self):
        resp = self.client.get(reverse("dashboard:players") + "?sort=invalid_field")
        self.assertEqual(resp.status_code, 200)
        players = list(resp.context["players"])
        self.assertEqual(players[0].username, "Ash")

    def test_context_has_current_sort(self):
        resp = self.client.get(reverse("dashboard:players") + "?sort=pokemons_caught")
        self.assertEqual(resp.context["current_sort"], "pokemons_caught")

    def test_context_has_sort_fields(self):
        resp = self.client.get(reverse("dashboard:players"))
        self.assertIn("sort_fields", resp.context)
        self.assertIn("pokemons_caught", resp.context["sort_fields"])


@tag("integration")
class WikiEditViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")
        self.page = WikiPage.objects.create(
            slug="edit-me", title="Edit Me", content="Original content."
        )

    def test_edit_get_returns_200(self):
        resp = self.client.get(reverse("dashboard:wiki-edit", args=["edit-me"]))
        self.assertEqual(resp.status_code, 200)

    def test_edit_post_updates_page(self):
        self.client.post(
            reverse("dashboard:wiki-edit", args=["edit-me"]),
            {"title": "Updated Title", "slug": "edit-me", "content": "New content."},
        )
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, "Updated Title")
        self.assertEqual(self.page.content, "New content.")

    def test_edit_redirects_to_list(self):
        resp = self.client.post(
            reverse("dashboard:wiki-edit", args=["edit-me"]),
            {"title": "Updated", "slug": "edit-me", "content": "Content."},
        )
        self.assertRedirects(resp, reverse("dashboard:wiki-list"))

    def test_edit_404_on_unknown_slug(self):
        resp = self.client.get(reverse("dashboard:wiki-edit", args=["does-not-exist"]))
        self.assertEqual(resp.status_code, 404)


@tag("integration")
class TriggerCollectionViewTest(TestCase):
    def setUp(self):
        _staff_user()
        self.client.login(username="staff", password="pass")

    def test_post_redirects_to_logs(self):
        with patch("features.collector.tasks.run_collection"):
            resp = self.client.post(reverse("dashboard:trigger"))
        self.assertRedirects(resp, reverse("dashboard:logs"))

    def test_post_success_adds_success_message(self):
        with patch("features.collector.tasks.run_collection"):
            resp = self.client.post(reverse("dashboard:trigger"), follow=True)
        messages = list(resp.context["messages"])
        self.assertTrue(any("successfully" in str(m) for m in messages))

    def test_post_failure_adds_error_message(self):
        with patch(
            "features.collector.tasks.run_collection",
            side_effect=Exception("SFTP failed"),
        ):
            resp = self.client.post(reverse("dashboard:trigger"), follow=True)
        messages = list(resp.context["messages"])
        self.assertTrue(any("failed" in str(m).lower() for m in messages))
