import os
import sys

from django.apps import AppConfig


class CollectorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.collector"

    def ready(self):
        from django.conf import settings
        if settings.TESTING:
            return
        # In Django's dev server, ready() is called twice (reloader parent + child).
        # RUN_MAIN is set only in the child process that actually serves requests.
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return
        from apps.collector.tasks import start_scheduler
        start_scheduler()
