"""Create a batch of placeholder AstroImage records for non-production environments."""

from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from typing import cast

from PIL import Image

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from astrophotography.models import AstroImage, Place


class Command(BaseCommand):
    help = "Create placeholder AstroImage records in batch."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of AstroImage records to create. Defaults to 10.",
        )

    def handle(self, *args, **options) -> None:
        del args
        count = options["count"]
        if count < 1:
            self.stderr.write(self.style.ERROR("--count must be greater than 0."))
            return

        place = self._get_or_create_batch_place()
        created_images: list[AstroImage] = []
        starting_index = AstroImage.objects.count() + 1

        for offset in range(count):
            index = starting_index + offset
            image = self._build_astro_image(place=place, index=index)
            created_images.append(image)

        self.stdout.write(
            self.style.SUCCESS(
                "Created "
                f"{len(created_images)} AstroImage record(s) "
                f"starting from index {starting_index}."
            )
        )

    def _get_or_create_batch_place(self) -> Place:
        place = cast(
            Place | None,
            Place.objects.translated("en", name="Batch Observatory").first(),
        )
        if place:
            return place

        place = Place(country="PL")
        place.set_current_language("en")
        place.name = "Batch Observatory"
        place.save()

        place.set_current_language("pl")
        place.name = "Obserwatorium testowe"
        place.save()

        return place

    def _build_astro_image(self, *, place: Place, index: int) -> AstroImage:
        image_content = self._generate_placeholder_image(index=index)
        file_name = f"batch-astro-image-{index}.png"

        image = AstroImage(
            place=place,
            celestial_object="Deep Sky",
            astrobin_url=f"https://example.com/astro/{index}",
            capture_date=timezone.now().date() - timedelta(days=index - 1),
        )
        image.original.save(file_name, ContentFile(image_content), save=False)
        image.path.save(file_name, ContentFile(image_content), save=False)

        image.set_current_language("en")
        image.name = f"Batch Astro Image {index}"
        image.description = (
            f"Placeholder astrophotography image {index} for gallery pagination checks."
        )
        image.exposure_details = "60x300s, Gain 100"
        image.processing_details = "Generated via management command"
        image.save()

        image.set_current_language("pl")
        image.name = f"Testowy obraz astro {index}"
        image.description = (
            f"Zastępczy obraz astrofotograficzny {index} do sprawdzania paginacji galerii."
        )
        image.exposure_details = "60x300s, Gain 100"
        image.processing_details = "Wygenerowany przez komendę zarządzającą"
        image.save()

        return image

    @staticmethod
    def _generate_placeholder_image(*, index: int) -> bytes:
        image = Image.new(
            "RGB",
            (1600, 900),
            color=((20 + index * 7) % 255, (35 + index * 11) % 255, (60 + index * 13) % 255),
        )
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
