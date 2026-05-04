from django.contrib import admin
from django.utils.html import format_html

from .models import Mod


@admin.register(Mod)
class ModAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "category", "thumbnail_preview", "mod_url")
    list_filter = ("category",)
    search_fields = ("name", "description")
    readonly_fields = ("slug", "thumbnail_preview")

    def thumbnail_preview(self, obj: Mod) -> str:
        if obj.thumbnail:
            return format_html(
                '<img src="{}" height="48" style="border-radius:4px">',
                obj.thumbnail.url,
            )
        return "—"

    thumbnail_preview.short_description = "Preview"
