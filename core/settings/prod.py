import os
from .base import *  # noqa: F403, F405

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ.get("POSTGRES_HOST", "cobblemon_db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h]
FORCE_SCRIPT_NAME = "/cobblemon-returns"
USE_X_FORWARDED_HOST = True
CSRF_COOKIE_PATH = "/cobblemon-returns/"
SESSION_COOKIE_PATH = "/cobblemon-returns/"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
