from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, tag

from features.mods.models import Mod
from features.mods.services.packwiz_service import ModrinthData, PackwizEntry


def _make_mod(**kwargs) -> Mod:
    defaults = {
        "name": "Test Mod",
        "version": "1.0.0",
        "description": "A test mod",
        "mod_url": "https://modrinth.com/mod/test",
        "category": "core",
    }
    defaults.update(kwargs)
    return Mod.objects.create(**defaults)


def _data(mid, name, version="2.0.0"):
    return ModrinthData(
        modrinth_id=mid,
        name=name,
        version=version,
        description="desc",
        body="body",
        icon_url="",  # empty → no thumbnail download
        mod_url=f"https://modrinth.com/mod/{name.lower()}",
        mod_wiki="",
        dependencies=[],
    )


def _run(entries, enriched, prune=False):
    with (
        patch("features.mods.services.packwiz_service.refresh_snapshot"),
        patch(
            "features.mods.services.packwiz_service.fetch_pack_entries",
            return_value=entries,
        ),
        patch(
            "features.mods.services.packwiz_service.enrich_from_modrinth",
            return_value=enriched,
        ),
    ):
        args = ["sync_from_packwiz"]
        if prune:
            args.append("--prune")
        call_command(*args)


@tag("integration")
class SyncCommandTest(TestCase):
    def test_creates_new_mod_from_modrinth(self):
        entries = [
            PackwizEntry(
                "appleskin.pw.toml", "AppleSkin", "modrinth", "AAA", "v", "client"
            )
        ]
        _run(entries, {"AAA": _data("AAA", "AppleSkin")})

        mod = Mod.objects.get(modrinth_id="AAA")
        self.assertEqual(mod.name, "AppleSkin")
        self.assertEqual(mod.version, "2.0.0")
        self.assertEqual(mod.category, "client-side")  # from side=client

    def test_updates_api_fields_but_preserves_editorial(self):
        _make_mod(
            name="AppleSkin",
            modrinth_id="AAA",
            category="core",
            tags=["pokemon"],
            description_pt_br="tradução",
            version="1.0.0",
        )
        entries = [
            PackwizEntry("appleskin.pw.toml", "AppleSkin", "modrinth", "AAA", "v")
        ]
        _run(entries, {"AAA": _data("AAA", "AppleSkin New", version="9.9.9")})

        mod = Mod.objects.get(modrinth_id="AAA")
        self.assertEqual(mod.name, "AppleSkin New")  # API field updated
        self.assertEqual(mod.version, "9.9.9")
        self.assertEqual(mod.category, "core")  # editorial preserved
        self.assertEqual(mod.tags, ["pokemon"])
        self.assertEqual(mod.description_pt_br, "tradução")

    def test_backfills_modrinth_id_by_name(self):
        _make_mod(name="AppleSkin", modrinth_id="")
        entries = [
            PackwizEntry("appleskin.pw.toml", "AppleSkin", "modrinth", "AAA", "v")
        ]
        _run(entries, {"AAA": _data("AAA", "AppleSkin")})

        self.assertEqual(Mod.objects.count(), 1)
        self.assertEqual(Mod.objects.get().modrinth_id, "AAA")

    def test_jar_entry_is_skipped(self):
        entries = [PackwizEntry("MyMod.jar", "MyMod", "jar")]
        _run(entries, {})
        self.assertEqual(Mod.objects.count(), 0)

    def test_removed_not_deleted_without_prune(self):
        _make_mod(name="Ghost", modrinth_id="GHOST")
        _run([], {})
        self.assertTrue(Mod.objects.filter(modrinth_id="GHOST").exists())

    def test_removed_deleted_with_prune(self):
        _make_mod(name="Ghost", modrinth_id="GHOST")
        _run([], {}, prune=True)
        self.assertFalse(Mod.objects.filter(modrinth_id="GHOST").exists())

    def test_jar_mod_not_flagged_removed(self):
        # A manually-added mod matching a jar entry by name should survive prune.
        _make_mod(name="MyMod", modrinth_id="")
        entries = [PackwizEntry("MyMod.jar", "MyMod", "jar")]
        _run(entries, {}, prune=True)
        self.assertTrue(Mod.objects.filter(name="MyMod").exists())
