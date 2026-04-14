from django.shortcuts import render


def discord_card(request, ranking_id="hours"):
    return render(request, "rankings/discord_card.html", {"ranking_id": ranking_id})
