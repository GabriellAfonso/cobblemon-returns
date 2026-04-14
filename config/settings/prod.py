import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db.sqlite3",
    }
}

FORCE_SCRIPT_NAME = "/cobblemon-returns"
USE_X_FORWARDED_HOST = True
STATIC_URL = "/cobblemon-returns/static/"
STATIC_ROOT = "/data/static/"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
