"""Rebuild thumbnail files for portfolio image models.

This command regenerates thumbnails from the current source image and the
current thumbnail settings, which is useful after quality or sizing changes.
"""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage, MainPageBackgroundImage
from common.utils.image import delete_file_from_storage
from programming.models import ProjectImage


class Command(BaseCommand):
    """Recreate model thumbnails using the current thumbnail generation logic."""

    help = "Regenerate thumbnails for all portfolio models using the latest quality/size settings."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate all thumbnails even if they already exist.",
        )

    def handle(self, *args, **options) -> None:
        force: bool = options["force"]
        models_to_process = [
            ("AstroImage", AstroImage.objects.all()),
            ("MainPageBackgroundImage", MainPageBackgroundImage.objects.all()),
            ("ProjectImage", ProjectImage.objects.all()),
        ]

        total_regenerated = 0
        total_skipped = 0
        total_errors = 0

        for model_name, queryset in models_to_process:
            self.stdout.write(f"\nProcessing {model_name}...")
            for obj in queryset:
                try:
                    thumb_source = obj.original_field

                    if not thumb_source:
                        self.stdout.write(f"  [SKIP] {obj} - No image source")
                        total_skipped += 1
                        continue

                    if obj.thumbnail and not force:
                        self.stdout.write(f"  [SKIP] {obj} - Thumbnail exists")
                        total_skipped += 1
                        continue

                    self.stdout.write(f"  [GEN ] {obj}")

                    thumb_content: ContentFile = obj.make_thumbnail(thumb_source)

                    # Save the new thumbnail
                    if obj.thumbnail:
                        # Clean up old file if it exists and has a different name
                        old_name = obj.thumbnail.name
                        if old_name != thumb_content.name:
                            delete_file_from_storage(obj.thumbnail, old_name)

                    obj.thumbnail.save(thumb_content.name, thumb_content, save=True)
                    total_regenerated += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"  [ERR ] {obj}: {str(e)}"))
                    total_errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nFinished. Regenerated: {total_regenerated} | "
                f"Skipped: {total_skipped} | Errors: {total_errors}"
            )
        )
