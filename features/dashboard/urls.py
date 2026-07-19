from django.urls import path

from .views import (
    CollectionLogView,
    DashboardHomeView,
    PackwizOverviewView,
    PackwizRefreshView,
    PackwizSyncView,
    PlayersListView,
    TriggerCollectionView,
    TriggerDiscordRankingsView,
    WikiCreateView,
    WikiDeleteView,
    WikiEditView,
    WikiManageView,
)

app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("wiki/", WikiManageView.as_view(), name="wiki-list"),
    path("wiki/new/", WikiCreateView.as_view(), name="wiki-create"),
    path("wiki/<slug:slug>/edit/", WikiEditView.as_view(), name="wiki-edit"),
    path("wiki/<slug:slug>/delete/", WikiDeleteView.as_view(), name="wiki-delete"),
    path("logs/", CollectionLogView.as_view(), name="logs"),
    path("players/", PlayersListView.as_view(), name="players"),
    path("packwiz/", PackwizOverviewView.as_view(), name="packwiz"),
    path("packwiz/refresh/", PackwizRefreshView.as_view(), name="packwiz-refresh"),
    path("packwiz/sync/", PackwizSyncView.as_view(), name="packwiz-sync"),
    path("trigger-collection/", TriggerCollectionView.as_view(), name="trigger"),
    path(
        "trigger-discord-rankings/",
        TriggerDiscordRankingsView.as_view(),
        name="trigger-discord-rankings",
    ),
]
