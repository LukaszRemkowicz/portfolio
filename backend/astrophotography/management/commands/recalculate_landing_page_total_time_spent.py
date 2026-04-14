"""Recalculate the persisted landing page astrophotography total time spent."""

from django.core.management.base import BaseCommand
from django.db.models import Sum

from astrophotography.models import AstroImage
from astrophotography.tasks import calculate_astroimage_exposure_hours_task
from common.tasks import invalidate_frontend_ssr_cache_task
from core.cache_service import CacheService


class Command(BaseCommand):
    help = "Calculate per-image exposure hours for the landing-page total."

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

        CacheService.invalidate_landing_page_cache()
        invalidate_frontend_ssr_cache_task.delay(["settings"])
        aggregate = AstroImage.objects.aggregate(total=Sum("calculated_exposure_hours"))
        total_hours = float(aggregate["total"] or 0)
        action = "Rebuilt" if recalculate else "Calculated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} total time spent: {total_hours}h from {processed_images} image(s)."
            )
        )
