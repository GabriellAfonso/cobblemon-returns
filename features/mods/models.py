import os

from django.db import models


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
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField()
    description_pt_br = models.TextField(blank=True)
    mod_url = models.URLField()
    mod_wiki = models.URLField(blank=True)
    dependencies = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list)
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
        if self.pk:
            try:
                old = Mod.objects.get(pk=self.pk)
                if old.thumbnail and old.thumbnail != self.thumbnail:
                    old.thumbnail.delete(save=False)
            except Mod.DoesNotExist:
                pass
        super().save(*args, **kwargs)
