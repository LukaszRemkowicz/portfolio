from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clears the entire Django cache"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing cache...")
        cache.clear()
        self.stdout.write(self.style.SUCCESS("Successfully cleared cache"))
