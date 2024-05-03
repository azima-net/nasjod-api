import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Django command to pause execution until db is available"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_conn = None
        retry = 0
        while not db_conn and retry <= settings.MAX_RETRIES_DB:
            try:
                db_conn = connections["default"]
            except OperationalError:
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
