from django.test import TestCase, tag
from django.urls import reverse

from features.mods.models import Mod


def _make_mod(**kwargs) -> Mod:
    defaults = {
        "slug": "test-mod",
        "name": "Test Mod",
        "version": "1.0.0",
        "description": "A test mod",
        "mod_url": "https://modrinth.com/mod/test",
        "mod_wiki": "",
        "dependencies": [],
        "category": "core",
        "thumbnail": "",
    }
    defaults.update(kwargs)
    return Mod.objects.create(**defaults)


@tag("unit")
class ModModelTest(TestCase):
    def test_str(self):
        mod = _make_mod()
        self.assertEqual(str(mod), "Test Mod (core)")

    def test_default_ordering(self):
        _make_mod(slug="z-mod", name="Zzz Mod")
        _make_mod(slug="a-mod", name="Aaa Mod")
        names = list(Mod.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Aaa Mod", "Zzz Mod"])

    def test_dependencies_default_list(self):
        mod = _make_mod()
        self.assertIsInstance(mod.dependencies, list)

    def test_mod_wiki_optional(self):
        mod = _make_mod(mod_wiki="")
        self.assertEqual(mod.mod_wiki, "")


@tag("integration")
class ModsListViewTest(TestCase):
    def setUp(self):
        _make_mod(slug="core-mod", name="Core Mod", category="core")
        _make_mod(slug="client-mod", name="Client Mod", category="client-side")
        _make_mod(slug="server-mod", name="Server Mod", category="server-side")

    def test_default_shows_core(self):
        resp = self.client.get(reverse("mods:mods-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["current_category"], "core")
        self.assertContains(resp, "Core Mod")
        self.assertNotContains(resp, "Client Mod")

    def test_category_filter_client(self):
        resp = self.client.get(reverse("mods:mods-list") + "?category=client-side")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Client Mod")
        self.assertNotContains(resp, "Core Mod")

    def test_invalid_category_falls_back_to_core(self):
        resp = self.client.get(reverse("mods:mods-list") + "?category=bogus")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["current_category"], "core")

    def test_categories_in_context(self):
        resp = self.client.get(reverse("mods:mods-list"))
        ids = [c["id"] for c in resp.context["categories"]]
        self.assertIn("core", ids)
        self.assertIn("server-side", ids)
        self.assertIn("client-side", ids)
