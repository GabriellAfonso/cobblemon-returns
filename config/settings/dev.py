import os

from .base import *  # noqa: F403, F405

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / os.environ.get("DB_NAME", "db.sqlite3"),  # noqa: F405
    }
}

STATIC_ROOT = BASE_DIR / "static"  # noqa: F405
