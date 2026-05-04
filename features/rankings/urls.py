from django.urls import path

from .views import RankingsView

app_name = "rankings"

urlpatterns = [
    path("", RankingsView.as_view(), name="rankings"),
]
