from django.apps import AppConfig
import os

class DashboardConfig(AppConfig):
    name = 'dashboard'

    def ready(self):
        # Prevent the scheduler from running twice in development mode
        if os.environ.get('RUN_MAIN'):
            from . import updater
            updater.start()