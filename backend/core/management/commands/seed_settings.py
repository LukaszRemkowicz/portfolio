from django.core.management.base import BaseCommand

from astrophotography.models import MeteorsMainPageConfig
from core.models import LandingPageSettings


class Command(BaseCommand):
    help = "Seed initial landing page settings and meteors configuration if they don't exist."

    def handle(self, *args, **options):
        self.stdout.write("Seeding landing page settings...")

        # Get or Create Meteors Config
        meteors_config = MeteorsMainPageConfig.objects.last()
        if not meteors_config:
            meteors_config = MeteorsMainPageConfig.objects.create()
            self.stdout.write(
                self.style.SUCCESS(f"Created new Meteors Config: ID={meteors_config.id}")
            )
        else:
            self.stdout.write(f"Existing Meteors Config found: ID={meteors_config.id}")

        # Get or Create Landing Page Settings
        settings = LandingPageSettings.objects.last()
        if not settings:
            settings = LandingPageSettings.objects.create(meteors=meteors_config)
            self.stdout.write(
                self.style.SUCCESS(f"Created new Landing Page Settings: ID={settings.id}")
            )
        else:
            self.stdout.write(f"Existing Landing Page Settings found: ID={settings.id}")
            # Ensure Linkage
            if not settings.meteors:
                settings.meteors = meteors_config
                settings.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Successfully linked Meteors Configuration to Landing Page Settings."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Landing Page Settings already linked to Meteors Configuration."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
