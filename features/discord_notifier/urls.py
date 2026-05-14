from django.urls import path

from .views import discord_card_preview

app_name = "discord_notifier"

urlpatterns = [
    path("preview/<str:ranking_id>/", discord_card_preview, name="card-preview"),
]
