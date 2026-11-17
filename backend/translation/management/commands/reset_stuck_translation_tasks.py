from django.core.management.base import BaseCommand
from django.utils import timezone

from translation.models import TranslationTask


class Command(BaseCommand):
    help = "Mark translation tasks interrupted by a previous process as failed."

    def handle(self, *args, **options):
        count = TranslationTask.objects.filter(
            status__in=[TranslationTask.Status.PENDING, TranslationTask.Status.RUNNING]
        ).update(
            status=TranslationTask.Status.FAILED,
            error_message="Translation interrupted by process shutdown; retry this translation.",
            updated_at=timezone.now(),
        )
        self.stdout.write(f"Marked {count} interrupted translation task(s) as failed.")
