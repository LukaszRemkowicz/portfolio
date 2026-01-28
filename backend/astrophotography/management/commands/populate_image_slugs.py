# backend/astrophotography/management/commands/populate_image_slugs.py
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import slugify
from astrophotography.models import AstroImage

class Command(BaseCommand):
    help = "Populate slugs for AstroImage objects that don't have one."

    # TODO: Remove this command once all environments have been migrated and data is consistent.
    # This is a temporary solution to avoid data population logic in migration files.

    def handle(self, *args, **options):
        self.stdout.write("Populating slugs for AstroImage...")
        images_to_update = AstroImage.objects.filter(models.Q(slug__isnull=True) | models.Q(slug=""))
        
        count = 0
        for image in AstroImage.objects.all():
            if not image.slug:
                base_slug = slugify(image.name)
                slug = base_slug
                n = 1
                while AstroImage.objects.filter(slug=slug).exclude(pk=image.pk).exists():
                    slug = f"{base_slug}-{n}"
                    n += 1
                image.slug = slug
                image.save()
                count += 1
                self.stdout.write(f"Updated: {image.name} -> {image.slug}")

        self.stdout.write(self.style.SUCCESS(f"Successfully populated {count} slugs."))
