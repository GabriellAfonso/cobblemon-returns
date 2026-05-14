from django.http import Http404
from django.shortcuts import render
from django.utils import timezone


def discord_card_preview(request, ranking_id):
    from features.discord_notifier.screenshot import _icon_data_uri
    from features.players.repositories.stats_repository import PlayerStatsRepository
    from features.rankings.config import RANKINGS
    from features.rankings.formatters import format_value

    ranking = next((r for r in RANKINGS if r["id"] == ranking_id), None)
    if not ranking:
        raise Http404

    stats_repo = PlayerStatsRepository()
    top10 = stats_repo.get_top_by_field(ranking["field"])
    players = [
        {
            "name": stat.player.username,
            "value": format_value(getattr(stat, ranking["field"]), ranking["format"]),
        }
        for stat in top10
    ]

    ranking_ctx = {
        **ranking,
        "icon_data_uri": _icon_data_uri(ranking.get("icon_img", "")),
    }

    return render(
        request,
        "rankings/discord_card.html",
        {
            "ranking": ranking_ctx,
            "players": players,
            "date": timezone.localtime().strftime("%d/%m/%Y · %H:%M"),
            "SERVER_HOST": request.build_absolute_uri("/").rstrip("/"),
        },
    )
