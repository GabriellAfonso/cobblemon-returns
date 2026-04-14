from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
from django.urls import include, path


def health(request):
    return HttpResponse("ok", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("", include("apps.rankings.urls")),
    path("players/", include("apps.players.urls")),
    path("wiki/", include("apps.wiki.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("collector/", include("apps.collector.urls")),
    path("discord/", include("apps.discord_notifier.urls")),
] + staticfiles_urlpatterns()
