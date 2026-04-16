import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "features.players",
    "features.rankings",
    "features.collector",
    "features.discord_notifier",
    "features.wiki",
    "features.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "features.rankings.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TESTING = "test" in sys.argv

# Server
SERVER_HOST = os.environ.get("SERVER_HOST", "")

# SFTP
SFTP_HOST = os.environ.get("SFTP_HOST", "")
SFTP_PORT = os.environ.get("SFTP_PORT", "22")
SFTP_USER = os.environ.get("SFTP_USER", "")
SFTP_KEY_PATH = os.environ.get("SFTP_KEY_PATH", "/run/secrets/sftp_key")

# Minecraft file paths
MINECRAFT_WORLD_PATH = os.environ.get("MINECRAFT_WORLD_PATH", "")
COBBLEMON_DATA_PATH = os.environ.get("COBBLEMON_DATA_PATH", "")
COBBLE_ECONOMY_PATH = os.environ.get("COBBLE_ECONOMY_PATH", "")
COBBLE_TCG_PATH = os.environ.get("COBBLE_TCG_PATH", "")

# Collector
COLLECTOR_INTERVAL_MINUTES = int(os.environ.get("COLLECTOR_INTERVAL_MINUTES", "15"))

# Discord
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
DISCORD_INVITE_URL = os.environ.get(
    "DISCORD_INVITE_URL", "https://discord.gg/cyx2d2Vtey"
)
DISCORD_RANKING_HOUR = int(os.environ.get("DISCORD_RANKING_HOUR", "20"))
