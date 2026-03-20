"""Clear the configured Django cache backend.

Use this command after content, metadata, or serving behavior changes when a
full cache reset is preferred over targeted invalidation.
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Flush the active Django cache backend."""

    help = "Clears the entire Django cache"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing cache...")
        cache.clear()
        self.stdout.write(self.style.SUCCESS("Successfully cleared cache"))
