from django.contrib import admin

from .models import Player, PlayerStats


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("uuid", "username", "last_seen", "hidden")
    list_filter = ("hidden",)
    list_editable = ("hidden",)
    search_fields = ("username", "uuid")


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "play_time_ticks",
        "pokemons_caught",
        "pokedex_registered",
        "battles_won",
        "cobbledollars",
        "updated_at",
    )
    search_fields = ("player__username",)
