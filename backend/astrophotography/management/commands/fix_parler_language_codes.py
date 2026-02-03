from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage, MainPageLocation, Place


class Command(BaseCommand):
    """TODO: Remove this command after the migration is complete."""

    help = "Migrates Parler translation language codes from 'en-us' to 'en'."

    def handle(self, *args, **options):
        self.stdout.write(
            "Starting migration of translation language codes from 'en-us' to 'en'..."
        )

        # Models that have Parler translations
        models_to_check = [
            (AstroImage, "AstroImage"),
            (Place, "Place"),
            (MainPageLocation, "MainPageLocation"),
        ]

        total_fixed = 0
        for model, name in models_to_check:
            self.stdout.write(f"\nChecking {name}...")

            # Parler creates a separate model for translations.
            # We access it via the 'translations' related name on the master model.
            # However, for batch updates, it's more efficient to query the translation model directly.  # noqa: E501
            translation_model = model._parler_meta.root_model

            count = translation_model.objects.filter(language_code="en-us").update(
                language_code="en"
            )
            self.stdout.write(self.style.SUCCESS(f"  Fixed {count} {name} translations."))
            total_fixed += count

        self.stdout.write(
            self.style.SUCCESS(f"\nMigration complete. Total translations fixed: {total_fixed}")
        )
