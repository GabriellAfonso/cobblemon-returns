import io
import tarfile
from unittest.mock import patch

from django.test import TestCase, tag

from features.mods.models import Mod
from features.mods.services import packwiz_service as ps
from features.mods.services.packwiz_service import PackwizEntry


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


def _build_tarball(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buf.getvalue()


class _Resp:
    def __init__(self, content=b"", json_data=None, status_code=200):
        self.content = content
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


_MODRINTH_TOML = b"""
name = "AppleSkin"
side = "both"
[update]
[update.modrinth]
mod-id = "EsAfCjCV"
version = "b5ZiCjAr"
"""

_CURSEFORGE_TOML = b"""
name = "Framework"
side = "both"
[update]
[update.curseforge]
file-id = 7530359
project-id = 549225
"""


@tag("unit")
class ParsePwTomlTest(TestCase):
    def test_modrinth_entry(self):
        entry = ps._parse_pw_toml("appleskin.pw.toml", _MODRINTH_TOML)
        self.assertEqual(entry.source, "modrinth")
        self.assertEqual(entry.name, "AppleSkin")
        self.assertEqual(entry.modrinth_id, "EsAfCjCV")
        self.assertEqual(entry.version_id, "b5ZiCjAr")
        self.assertEqual(entry.side, "both")

    def test_curseforge_entry(self):
        entry = ps._parse_pw_toml("framework.pw.toml", _CURSEFORGE_TOML)
        self.assertEqual(entry.source, "curseforge")
        self.assertEqual(entry.name, "Framework")
        self.assertEqual(entry.modrinth_id, "")


@tag("unit")
class FetchPackEntriesTest(TestCase):
    def test_parses_modrinth_curseforge_and_jar(self):
        tarball = _build_tarball(
            {
                "repo-master/mods/appleskin.pw.toml": _MODRINTH_TOML,
                "repo-master/mods/framework.pw.toml": _CURSEFORGE_TOML,
                "repo-master/mods/MyMod.jar": b"binary",
                "repo-master/mods/nested/skip.pw.toml": _MODRINTH_TOML,
                "repo-master/config/foo.toml": b"nope",
            }
        )
        with patch.object(ps.requests, "get", return_value=_Resp(content=tarball)):
            entries = ps.fetch_pack_entries()

        sources = {e.name: e.source for e in entries}
        self.assertEqual(sources.get("AppleSkin"), "modrinth")
        self.assertEqual(sources.get("Framework"), "curseforge")
        self.assertEqual(sources.get("MyMod.jar"), "jar")
        # nested + non-mods files are ignored
        self.assertEqual(len(entries), 3)


@tag("unit")
class ClassifyPackTest(TestCase):
    def test_buckets(self):
        synced_mod = _make_mod(name="AppleSkin", modrinth_id="EsAfCjCV")
        removed_mod = _make_mod(name="Old Mod", modrinth_id="GONE123")
        jar_mod = _make_mod(name="MyMod", modrinth_id="")

        entries = [
            PackwizEntry("appleskin.pw.toml", "AppleSkin", "modrinth", "EsAfCjCV"),
            PackwizEntry("lib.pw.toml", "Some Library", "modrinth", "LIBID"),
            PackwizEntry("MyMod.jar", "MyMod", "jar"),
        ]
        overview = ps.classify_pack(entries, [synced_mod, removed_mod, jar_mod])

        self.assertEqual([i.name for i in overview.synced], ["AppleSkin"])
        self.assertEqual([i.name for i in overview.pack_only], ["Some Library"])
        self.assertEqual([i.name for i in overview.jar], ["MyMod"])
        self.assertEqual([i.name for i in overview.removed], ["Old Mod"])

    def test_name_fallback_when_no_id(self):
        mod = _make_mod(name="3D Skin Layers", modrinth_id="")
        entries = [
            PackwizEntry("3dskinlayers.pw.toml", "3D Skin Layers", "modrinth", "X")
        ]
        overview = ps.classify_pack(entries, [mod])
        self.assertEqual(len(overview.synced), 1)
        self.assertEqual(len(overview.removed), 0)


@tag("unit")
class EnrichFromModrinthTest(TestCase):
    def test_builds_modrinth_data(self):
        entries = [
            PackwizEntry(
                "appleskin.pw.toml", "AppleSkin", "modrinth", "EsAfCjCV", "verid"
            ),
            PackwizEntry("MyMod.jar", "MyMod", "jar"),
        ]

        def fake_get(url, params=None, headers=None, timeout=None):
            if url.endswith("/projects"):
                return _Resp(
                    json_data=[
                        {
                            "id": "EsAfCjCV",
                            "slug": "appleskin",
                            "title": "AppleSkin",
                            "description": "Food HUD",
                            "body": "long body",
                            "icon_url": "https://cdn/icon.png",
                            "source_url": "https://github.com/x",
                            "wiki_url": None,
                        }
                    ]
                )
            if "/version/" in url:
                return _Resp(
                    json_data={
                        "version_number": "3.0.6",
                        "dependencies": [
                            {"project_id": "DEP1", "dependency_type": "required"}
                        ],
                    }
                )
            return _Resp(json_data=[])

        with patch.object(ps.requests, "get", side_effect=fake_get):
            # DEP resolution also hits /projects; return empty for unknown deps
            result = ps.enrich_from_modrinth(entries, backoff=0)

        self.assertIn("EsAfCjCV", result)
        data = result["EsAfCjCV"]
        self.assertEqual(data.name, "AppleSkin")
        self.assertEqual(data.version, "3.0.6")
        self.assertEqual(data.mod_url, "https://modrinth.com/mod/appleskin")
        self.assertEqual(data.icon_url, "https://cdn/icon.png")
