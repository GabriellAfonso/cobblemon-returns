from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse

from features.mods.models import Mod, PackwizSnapshot

User = get_user_model()


def _staff_login(client):
    User.objects.create_user(username="staff", password="pass", is_staff=True)
    client.login(username="staff", password="pass")


def _make_mod(**kwargs) -> Mod:
    defaults = {
        "name": "AppleSkin",
        "version": "1.0.0",
        "description": "d",
        "mod_url": "https://modrinth.com/mod/appleskin",
        "category": "core",
    }
    defaults.update(kwargs)
    return Mod.objects.create(**defaults)


@tag("integration")
class PackwizOverviewViewTest(TestCase):
    def setUp(self):
        _staff_login(self.client)

    def test_empty_snapshot_shows_prompt(self):
        resp = self.client.get(reverse("dashboard:packwiz"))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["has_snapshot"])

    def test_classifies_from_snapshot(self):
        _make_mod(name="AppleSkin", modrinth_id="AAA")
        snap = PackwizSnapshot.load()
        snap.data = {
            "entries": [
                {
                    "filename": "appleskin.pw.toml",
                    "name": "AppleSkin",
                    "source": "modrinth",
                    "modrinth_id": "AAA",
                    "version_id": "v",
                    "side": "",
                },
                {
                    "filename": "MyMod.jar",
                    "name": "MyMod",
                    "source": "jar",
                    "modrinth_id": "",
                    "version_id": "",
                    "side": "",
                },
            ]
        }
        snap.save()

        resp = self.client.get(reverse("dashboard:packwiz"))
        overview = resp.context["overview"]
        self.assertEqual(len(overview.synced), 1)
        self.assertEqual(len(overview.jar), 1)


@tag("integration")
class PackwizRefreshViewTest(TestCase):
    def setUp(self):
        _staff_login(self.client)

    def test_refresh_redirects(self):
        with patch("features.mods.services.packwiz_service.refresh_snapshot"):
            resp = self.client.post(reverse("dashboard:packwiz-refresh"))
        self.assertRedirects(resp, reverse("dashboard:packwiz"))


@tag("integration")
class PackwizSyncViewTest(TestCase):
    def setUp(self):
        _staff_login(self.client)

    def test_sync_redirects_and_messages(self):
        with patch("django.core.management.call_command"):
            resp = self.client.post(reverse("dashboard:packwiz-sync"), follow=True)
        messages = list(resp.context["messages"])
        self.assertTrue(any("background" in str(m).lower() for m in messages))
