from django.contrib import admin

from .models import Player, PlayerStats


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("uuid", "username", "last_seen")
    search_fields = ("username", "uuid")


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "play_time_ticks",
        "pokemons_caught",
        "pokedex_registered",
        "cobbletcg_cards",
        "battles_won",
        "cobbledollars",
        "updated_at",
    )
    search_fields = ("player__username",)
