from django.utils.translation import gettext_lazy as _

RANKINGS = [
    {
        "id": "hours",
        "field": "play_time_ticks",
        "label": _("Hours Played"),
        "icon": "⏱️",
        "format": "hours",
    },
    {
        "id": "catches",
        "field": "pokemons_caught",
        "label": _("Pokémons Caught"),
        "icon": "🔴",
        "format": "number",
    },
    {
        "id": "pokedex",
        "field": "pokedex_registered",
        "label": _("Pokédex Registered"),
        "icon": "📕",
        "format": "number",
    },
    {
        "id": "cards",
        "field": "cobbletcg_cards",
        "label": _("CobbleTCG Cards"),
        "icon": "🃏",
        "format": "number",
    },
    {
        "id": "battles",
        "field": "battles_won",
        "label": _("Battles Won"),
        "icon": "⚔️",
        "format": "number",
    },
    {
        "id": "money",
        "field": "cobbledollars",
        "label": _("CobbleDollars"),
        "icon": "💰",
        "format": "currency",
    },
]
