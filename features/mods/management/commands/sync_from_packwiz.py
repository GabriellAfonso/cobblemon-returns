"""Sync the Mod catalog from the packwiz pack + Modrinth API.

- Modrinth entries: name/version/description/image/deps/url are pulled from the
  API and always refreshed. Editorial fields (category, tags, description_pt_br)
  are only set on creation and preserved on update.
- Jar / CurseForge entries: skipped and reported (need manual entry).
- Mods no longer in the pack: reported; deleted only with ``--prune``.
"""

import os
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from features.mods.models import Mod
from features.mods.services import packwiz_service
from features.mods.services.packwiz_service import _normalize

_SIDE_TO_CATEGORY = {
    "client": "client-side",
    "server": "server-side",
    "both": "core",
}
_DEFAULT_CATEGORY = "client-side"


class Command(BaseCommand):
    help = "Sync mods from the packwiz pack + Modrinth API into the database"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Delete mods that are no longer present in the pack.",
        )

    def handle(self, *args: object, **options: object) -> None:
        prune = bool(options.get("prune"))

        self.stdout.write("Fetching packwiz pack…")
        packwiz_service.refresh_snapshot()
        entries = packwiz_service.fetch_pack_entries()

        mods = list(Mod.objects.all())
        by_id = {m.modrinth_id: m for m in mods if m.modrinth_id}
        by_name = {_normalize(m.name): m for m in mods}
        matched: set[int] = set()

        self.stdout.write("Fetching Modrinth metadata…")
        enriched = packwiz_service.enrich_from_modrinth(entries)

        created = updated = skipped = 0

        for entry in entries:
            if entry.source != "modrinth":
                mod = self._find(entry, by_id, by_name)
                if mod:
                    matched.add(mod.pk)
                skipped += 1
                self.stdout.write(f"  skip (manual): {entry.name}")
                continue

            data = enriched.get(entry.modrinth_id)
            if data is None:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"  skip (no Modrinth data): {entry.name}")
                )
                continue

            mod = self._find(entry, by_id, by_name)
            is_new = mod is None
            if is_new:
                mod = Mod(
                    category=_SIDE_TO_CATEGORY.get(entry.side, _DEFAULT_CATEGORY),
                    tags=[],
                    description_pt_br="",
                )

            mod.modrinth_id = data.modrinth_id
            mod.name = data.name
            if not mod.slug:
                mod.slug = slugify(data.name)
            mod.version = data.version
            mod.description = data.description
            mod.mod_url = data.mod_url
            mod.mod_wiki = data.mod_wiki
            mod.dependencies = data.dependencies

            self._apply_thumbnail(mod, data.icon_url)
            mod.save()
            matched.add(mod.pk)

            if is_new:
                created += 1
            else:
                updated += 1

        removed = [m for m in mods if m.pk not in matched]
        self._report_removed(removed, prune)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — created: {created}, updated: {updated}, "
                f"skipped: {skipped}, removed: {len(removed)}"
            )
        )

    def _find(self, entry, by_id: dict, by_name: dict):
        if entry.modrinth_id and entry.modrinth_id in by_id:
            return by_id[entry.modrinth_id]
        return by_name.get(_normalize(entry.name))

    def _apply_thumbnail(self, mod: Mod, icon_url: str) -> None:
        if not icon_url:
            return
        try:
            resp = requests.get(icon_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.stdout.write(
                self.style.WARNING(f"  thumbnail failed for {mod.name}: {exc}")
            )
            return
        ext = os.path.splitext(urlparse(icon_url).path)[1] or ".png"
        slug = mod.slug or ""
        filename = f"{slug or 'mod'}-thumb{ext}"
        mod.thumbnail.save(filename, ContentFile(resp.content), save=False)

    def _report_removed(self, removed: list, prune: bool) -> None:
        if not removed:
            return
        label = "Deleting" if prune else "Not in pack (use --prune to delete)"
        self.stdout.write(self.style.WARNING(f"{label}:"))
        for mod in removed:
            self.stdout.write(f"  - {mod.name}")
        if prune:
            for mod in removed:
                mod.delete()
