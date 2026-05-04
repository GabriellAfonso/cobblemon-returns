from .base import *  # noqa: F403, F405

SECRET_KEY = "django-insecure-test-only"

DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Prevent scheduler from starting during tests (belt-and-suspenders with TESTING flag)
COLLECTOR_INTERVAL_MINUTES = 9999
DISCORD_RANKING_HOUR = 23
