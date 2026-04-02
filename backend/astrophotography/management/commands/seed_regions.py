"""Seed predefined travel and astrophotography regions into ``Place`` records.

The command creates region-level ``Place`` objects and links their known
sub-places. It is designed to be idempotent and safe to re-run.
"""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

from astrophotography.models import Place

# Region entries with country=None span multiple countries.
REGIONS: list[dict[str, Any]] = [
    {
        "name": "Scandinavia",
        "country": None,  # multi-country region
        "sub_places": [
            ("Norway", "NO"),
            ("Sweden", "SE"),
            ("Denmark", "DK"),
            ("Finland", "FI"),
        ],
    },
    {
        "name": "Hawaii",
        "country": "US",
        "sub_places": [
            ("Big Island", "US"),
            ("Oahu", "US"),
            ("Maui", "US"),
            ("Kauai", "US"),
            ("Molokai", "US"),
            ("Lanai", "US"),
        ],
    },
    {
        "name": "Canary Islands",
        "country": "ES",
        "sub_places": [
            ("Tenerife", "ES"),
            ("Gran Canaria", "ES"),
            ("Lanzarote", "ES"),
            ("Fuerteventura", "ES"),
            ("La Palma", "ES"),
            ("La Gomera", "ES"),
            ("El Hierro", "ES"),
        ],
    },
    {
        "name": "Baltic States",
        "country": None,
        "sub_places": [
            ("Estonia", "EE"),
            ("Latvia", "LV"),
            ("Lithuania", "LT"),
        ],
    },
    {
        "name": "Alps",
        "country": None,
        "sub_places": [
            ("Switzerland", "CH"),
            ("Austria", "AT"),
            ("Tyrol", "AT"),
            ("Bavaria", "DE"),
            ("Lombardy", "IT"),
            ("Haute-Savoie", "FR"),
            ("Slovenia", "SI"),
        ],
    },
]


def _get_or_create_place(place_name, country_code, lang):
    """
    Reliably get or create a Place by querying the translation table directly.
    Avoids the unreliable get_or_create with translations__name lookups.
    """
    # Look up via the Parler translation table using the base language
    existing = Place.objects.filter(
        translations__language_code=lang,
        translations__name=place_name,
        country=country_code,
    ).first()
    if existing:
        return existing, False

    place_obj = Place(country=country_code)
    place_obj.set_current_language(lang)
    place_obj.name = place_name
    place_obj.save()  # fires post_save → queues automated translations
    return place_obj, True


class Command(BaseCommand):
    """Populate region and sub-place data used by travel/highlight content."""

    help = (
        "Seeds known geographic regions and their sub-places into the database. "
        "Idempotent: safe to run multiple times. Uses the Parler base language."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be created without writing to the database.",
        )
        parser.add_argument(
            "--retranslate",
            action="store_true",
            help=(
                "Re-save all seeded sub-places and regions to re-trigger post_save "
                "signals and queue automated translations."
            ),
        )

    def handle(self, *args, **options):  # noqa: C901
        dry_run = options["dry_run"]
        retranslate = options["retranslate"]
        lang = settings.DEFAULT_APP_LANGUAGE
        translation.activate(lang)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be written.\n"))

        if retranslate:
            self._retranslate_all(lang)
            return

        for region_data in REGIONS:
            region_name = region_data["name"]
            region_country = region_data["country"]
            sub_places_data = region_data["sub_places"]

            # --- Create sub-place records first ---
            sub_place_objects = []
            for place_name, country_code in sub_places_data:
                if dry_run:
                    self.stdout.write(
                        f"  [DRY] Would create/get Place: {place_name} ({country_code})"
                    )
                    continue

                place_obj, created = _get_or_create_place(place_name, country_code, lang)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"  Created sub-place: {place_name} ({country_code})")
                    )
                else:
                    self.stdout.write(f"  Already exists: {place_name} ({country_code})")
                sub_place_objects.append(place_obj)

            # --- Create region record ---
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY] Would create/get Region: {region_name} "
                        f"(country={'None' if not region_country else region_country}, "
                        f"is_region=True)\n"
                    )
                )
                continue

            region_obj = Place.objects.filter(
                translations__language_code=lang,
                translations__name=region_name,
                is_region=True,
            ).first()

            if not region_obj:
                region_obj = Place(country=region_country or "", is_region=True)
                region_obj.set_current_language(lang)
                region_obj.name = region_name
                region_obj.save()  # fires post_save → queues automated translations
                self.stdout.write(self.style.SUCCESS(f"Created region: {region_name}"))
            else:
                self.stdout.write(f"Already exists: region {region_name}")

            # --- Wire sub-places ---
            current_sub_places = set(region_obj.sub_places.values_list("pk", flat=True))
            for sub_place_obj in sub_place_objects:
                if sub_place_obj.pk not in current_sub_places:
                    region_obj.sub_places.add(sub_place_obj)
                    self.stdout.write(f"  Linked: {sub_place_obj} → {region_name}")

            self.stdout.write("")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS("Done seeding regions."))

    def _retranslate_all(self, lang: str) -> None:
        """Re-save all seeded places and regions to re-queue translation tasks."""
        sub_place_names = {
            place_name for region_data in REGIONS for place_name, _ in region_data["sub_places"]
        }
        region_names = {region_data["name"] for region_data in REGIONS}
        all_names = sub_place_names | region_names

        places = Place.objects.filter(
            translations__language_code=lang,
            translations__name__in=all_names,
        ).distinct()

        for place in places:
            name = place.safe_translation_getter("name", language_code=lang, any_language=True)
            place.set_current_language(lang)
            place.save()
            self.stdout.write(self.style.SUCCESS(f"Re-saved: {name!r} (pk={place.pk})"))

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. Re-queued translations for {places.count()} places.")
        )
