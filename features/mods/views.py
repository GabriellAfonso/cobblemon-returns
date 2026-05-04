from django.views.generic import TemplateView

from .models import Mod

CATEGORIES = [
    {"id": "core", "label": "Core", "icon": "⚙️"},
    {"id": "server-side", "label": "Server-Side", "icon": "🖥️"},
    {"id": "client-side", "label": "Client-Side", "icon": "🎮"},
]
VALID_CATEGORIES = {c["id"] for c in CATEGORIES}

TAGS = [
    {"id": "decoration", "label": "Decoration", "icon": "🪑"},
    {"id": "economy", "label": "Economy", "icon": "💰"},
    {"id": "gameplay_control", "label": "Gameplay Control", "icon": "🎛️"},
    {"id": "performance", "label": "Performance", "icon": "⚡"},
    {"id": "pokemon", "label": "Pokémon", "icon": "🔴"},
    {"id": "quality_of_life", "label": "Quality of Life", "icon": "✨"},
    {"id": "roleplay", "label": "Roleplay", "icon": "🎭"},
    {"id": "worldgen", "label": "World Generation", "icon": "🌍"},
]
VALID_TAGS = {t["id"] for t in TAGS}


class ModsListView(TemplateView):
    template_name = "mods/list.html"

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)

        category = self.request.GET.get("category", "core")
        if category not in VALID_CATEGORIES:
            category = "core"

        tag = self.request.GET.get("tag", "")
        if tag not in VALID_TAGS:
            tag = ""

        qs = Mod.objects.filter(category=category)
        if tag:
            qs = qs.filter(tags__icontains=f'"{tag}"')

        ctx["mods"] = qs
        ctx["current_category"] = category
        ctx["current_tag"] = tag
        ctx["categories"] = CATEGORIES
        ctx["tags"] = TAGS
        return ctx
