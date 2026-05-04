import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from features.mods.models import Mod

METADATA_DIRS = {
    "core-metadata": "core",
    "client-metadata": "client-side",
    "server-metadata": "server-side",
}

THUMB_EXTENSIONS = (".png", ".webp", ".jpg", ".jpeg", ".jfif", ".gif")


class Command(BaseCommand):
    help = "Load mods from _metadata_mods/ into the database"

    def handle(self, *args: object, **options: object) -> None:
        base = settings.BASE_DIR
        metadata_root = base / "_metadata_mods"
        images_dest = Path(settings.MEDIA_ROOT) / "mods" / "thumbnails"
        images_dest.mkdir(parents=True, exist_ok=True)

        created = updated = skipped = 0

        for dir_name, category in METADATA_DIRS.items():
            source_dir = metadata_root / dir_name
            if not source_dir.exists():
                self.stdout.write(self.style.WARNING(f"  Missing: {source_dir}"))
                continue

            for json_file in sorted(source_dir.glob("*-info.json")):
                slug = json_file.stem.removesuffix("-info")
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    self.stdout.write(
                        self.style.ERROR(f"  Bad JSON {json_file.name}: {exc}")
                    )
                    skipped += 1
                    continue

                thumbnail_path = self._copy_thumbnail(source_dir, slug, images_dest)

                defaults = {
                    "name": data.get("name", slug),
                    "version": data.get("version", ""),
                    "description": data.get("description", ""),
                    "description_pt_br": data.get("description_pt_br", ""),
                    "mod_url": data.get("mod_url", ""),
                    "mod_wiki": data.get("mod_wiki", ""),
                    "dependencies": data.get("dependencies", []),
                    "tags": data.get("tags", []),
                    "category": category,
                    "thumbnail": thumbnail_path,
                }

                _, was_created = Mod.objects.update_or_create(
                    slug=slug, defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — created: {created}, updated: {updated}, skipped: {skipped}"
            )
        )

    def _copy_thumbnail(self, source_dir: Path, slug: str, dest_dir: Path) -> str:
        for ext in THUMB_EXTENSIONS:
            src = source_dir / f"{slug}-thumb{ext}"
            if src.exists():
                dest = dest_dir / f"{slug}-thumb{ext}"
                shutil.copy2(src, dest)
                return f"mods/thumbnails/{slug}-thumb{ext}"
        return ""
