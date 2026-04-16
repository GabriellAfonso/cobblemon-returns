from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
from django.urls import include, path


def health(request):
    return HttpResponse("ok", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("", include("features.home.urls")),
    path("rankings/", include("features.rankings.urls")),
    path("players/", include("features.players.urls")),
    path("wiki/", include("features.wiki.urls")),
    path("dashboard/", include("features.dashboard.urls")),
    path("collector/", include("features.collector.urls")),
    path("discord/", include("features.discord_notifier.urls")),
] + staticfiles_urlpatterns()
