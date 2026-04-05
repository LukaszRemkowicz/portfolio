"""Recalculate the persisted landing page astrophotography total time spent."""

from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage
from core.tasks import (
    calculate_astroimage_exposure_hours_task,
    recalculate_landing_page_total_time_spent_task,
)


class Command(BaseCommand):
    help = "Calculate per-image exposure hours and recalculate the landing page total."

    def add_arguments(self, parser):
        parser.add_argument(
            "--recalculate",
            action="store_true",
            help=(
                "Recalculate exposure hours for all AstroImage records, "
                "including already calculated ones."
            ),
        )

    def handle(self, *args, **options):
        del args
        recalculate = options["recalculate"]
        processed_images = 0

        queryset = AstroImage.objects.all().order_by("pk")
        if recalculate:
            AstroImage.objects.update(calculated_exposure_hours=0)
        else:
            queryset = queryset.filter(calculated_exposure_hours=0)

        for image in queryset:
            calculate_astroimage_exposure_hours_task(str(image.pk))
            processed_images += 1

        total_result = recalculate_landing_page_total_time_spent_task()
        action = "Rebuilt" if recalculate else "Calculated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} total time spent: {total_result['total_time_spent']}h "
                f"from {processed_images} image(s)."
            )
        )
