import os

from django.db import models
from django.utils.text import slugify


def _thumbnail_upload_path(instance: "Mod", filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    return f"mods/thumbnails/{instance.slug}-thumb{ext}"


class Mod(models.Model):
    CATEGORY_CHOICES = [
        ("core", "Core"),
        ("server-side", "Server-Side"),
        ("client-side", "Client-Side"),
    ]

    slug = models.SlugField(unique=True)
    modrinth_id = models.CharField(max_length=20, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField()
    description_pt_br = models.TextField(blank=True)
    mod_url = models.URLField()
    mod_wiki = models.URLField(blank=True)
    dependencies = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    thumbnail = models.ImageField(
        upload_to=_thumbnail_upload_path, blank=True, null=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Mod"
        verbose_name_plural = "Mods"

    def __str__(self) -> str:
        return f"{self.name} ({self.category})"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        if self.pk:
            try:
                old = Mod.objects.get(pk=self.pk)
                if old.thumbnail and old.thumbnail != self.thumbnail:
                    old.thumbnail.delete(save=False)
            except Mod.DoesNotExist:
                pass
        super().save(*args, **kwargs)


class PackwizSnapshot(models.Model):
    """Singleton snapshot of the parsed packwiz pack state.

    Stored as a model (not cache) because no CACHES backend is configured and the
    dashboard needs a persistent ``updated_at`` to show "atualizado há X".
    """

    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Packwiz Snapshot"
        verbose_name_plural = "Packwiz Snapshot"

    def __str__(self) -> str:
        return f"PackwizSnapshot (updated {self.updated_at:%Y-%m-%d %H:%M})"

    @classmethod
    def load(cls) -> "PackwizSnapshot":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
