from django.conf import settings


def site_globals(request):
    return {
        "DISCORD_INVITE_URL": getattr(settings, "DISCORD_INVITE_URL", ""),
        "SERVER_HOST": getattr(settings, "SERVER_HOST", ""),
    }
