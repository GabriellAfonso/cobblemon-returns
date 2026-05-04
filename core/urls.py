from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
from django.urls import include, path


def health(request):
    return HttpResponse("ok", status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", health),
    path("", include("features.home.urls")),
    path("rankings/", include("features.rankings.urls")),
    path("players/", include("features.players.urls")),
    path("wiki/", include("features.wiki.urls")),
    path("mods/", include("features.mods.urls")),
    path("dashboard/", include("features.dashboard.urls")),
    path("collector/", include("features.collector.urls")),
    path("discord/", include("features.discord_notifier.urls")),
] + staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
