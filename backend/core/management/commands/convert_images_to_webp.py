"""Management command to batch-convert existing images to WebP format.

Usage:
    python manage.py convert_images_to_webp          # Convert all images
    python manage.py convert_images_to_webp --dry-run # Preview without changes

Safe to re-run: images that are already WebP or already have a legacy_path are skipped.
After running, flip LandingPageSettings.serve_webp_images = True in Django Admin.
"""

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage, MainPageBackgroundImage
from common.utils.image import convert_to_webp
from programming.models import ProjectImage
from users.models import User


class Command(BaseCommand):
    help = "Convert existing images to WebP and populate legacy_path for rollback."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview conversions without making any changes.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Re-convert already-converted images from their legacy_path (original) "
                "using the model's current webp_quality. Use after changing quality settings."
            ),
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made.\n"))
        if force:
            self.stdout.write(self.style.WARNING("FORCE MODE — re-converting from originals.\n"))

        total_converted = 0
        total_skipped = 0
        total_errors = 0

        # ---------- BaseImage subclasses ----------
        conv, skip, err = self._handle_base_images(dry_run, force)
        total_converted += conv
        total_skipped += skip
        total_errors += err

        # ---------- User image fields ----------
        conv, skip, err = self._handle_user_images(dry_run, force)
        total_converted += conv
        total_skipped += skip
        total_errors += err

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Converted: {total_converted} | "
                f"Skipped: {total_skipped} | "
                f"Errors: {total_errors}"
            )
        )

        if total_converted > 0 and not dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nNext step: In Django Admin → Landing Page Settings "
                    "→ enable 'Serve WebP Images' to start serving the converted files."
                )
            )
            call_command("clear_cache")

    def _handle_base_images(self, dry_run: bool, force: bool) -> tuple[int, int, int]:
        """Process all BaseImage subclasses. Returns (converted, skipped, errors)."""
        conv, skip, err = 0, 0, 0
        base_image_models = [
            ("AstroImage", AstroImage.objects.all()),
            ("MainPageBackgroundImage", MainPageBackgroundImage.objects.all()),
            ("ProjectImage", ProjectImage.objects.all()),
        ]

        for model_name, queryset in base_image_models:
            count = queryset.count()
            self.stdout.write(f"\n{model_name} ({count} records):")

            for obj in queryset:
                result = self._convert_base_image(obj, dry_run, force)
                if result == "converted":
                    conv += 1
                elif result == "skipped":
                    skip += 1
                else:
                    err += 1
        return conv, skip, err

    def _handle_user_images(self, dry_run: bool, force: bool) -> tuple[int, int, int]:
        """Process User model image fields. Returns (converted, skipped, errors)."""
        conv, skip, err = 0, 0, 0
        user = User.get_user()
        if not user:
            return 0, 0, 0

        self.stdout.write("\nUser images:")
        for field_name, legacy_field_name in [
            ("avatar", "avatar_legacy"),
            ("about_me_image", "about_me_image_legacy"),
            ("about_me_image2", "about_me_image2_legacy"),
        ]:
            result = self._convert_user_field(user, field_name, legacy_field_name, dry_run, force)
            if result == "converted":
                conv += 1
            elif result == "skipped":
                skip += 1
            else:
                err += 1
        return conv, skip, err

    def _convert_base_image(self, obj, dry_run: bool, force: bool = False) -> str:
        """Convert a BaseImage subclass instance. Returns 'converted', 'skipped', or 'error'."""
        name = str(obj)
        if not obj.path:
            self.stdout.write(f"  [SKIP] {name} — no path")
            return "skipped"

        current_name = str(obj.path.name)

        if current_name.lower().endswith(".webp") and not force:
            self.stdout.write(f"  [SKIP] {name} — already WebP")
            return "skipped"

        if obj.legacy_path and not force:
            self.stdout.write(f"  [SKIP] {name} — already has legacy_path")
            return "skipped"

        # In force mode, re-convert from the original (legacy_path) at the new quality.
        # If no legacy_path exists (first-time conversion), use obj.path as source.
        source = obj.legacy_path if (force and obj.legacy_path) else obj.path
        label = "RECONV" if (force and obj.legacy_path) else "CONV"
        self.stdout.write(f"  [{label}] {name} — {source.name}")

        if dry_run:
            return "converted"

        try:
            webp_quality: int = getattr(type(obj), "webp_quality", 90)

            result = convert_to_webp(source, quality=webp_quality)
            if result is None:
                self.stderr.write(self.style.ERROR(f"  [ERR ] {name} — conversion returned None"))
                return "error"
            original_name, webp_content = result
            # Save the new WebP, overwriting obj.path
            obj.path.save(webp_content.name, webp_content, save=False)
            if obj.path:
                thumb_content: ContentFile = obj.make_thumbnail(obj.path)
                obj.thumbnail.save(thumb_content.name, thumb_content, save=False)
            update_kwargs = {
                "path": str(obj.path.name) if obj.path else None,
                "thumbnail": str(obj.thumbnail.name) if obj.thumbnail else None,
            }
            # Only set legacy_path on first conversion (not on force re-conversion)
            if not force:
                update_kwargs["legacy_path"] = original_name
            type(obj).objects.filter(pk=obj.pk).update(**update_kwargs)
            return "converted"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {name} — {exc}"))
            return "error"

    def _convert_user_field(
        self,
        user: User,
        field_name: str,
        legacy_field_name: str,
        dry_run: bool,
        force: bool = False,
    ) -> str:
        """Convert a single User image field. Returns 'converted', 'skipped', or 'error'."""
        field = getattr(user, field_name)
        if not field:
            self.stdout.write(f"  [SKIP] {field_name} — empty")
            return "skipped"

        current_name = str(field.name)
        if current_name.lower().endswith(".webp") and not force:
            self.stdout.write(f"  [SKIP] {field_name} — already WebP")
            return "skipped"

        legacy = getattr(user, legacy_field_name)
        if legacy and not force:
            self.stdout.write(f"  [SKIP] {field_name} — already has legacy")
            return "skipped"

        # In force mode, re-convert from original (legacy) if available
        source = legacy if (force and legacy) else field
        label = "RECONV" if (force and legacy) else "CONV"
        self.stdout.write(f"  [{label}] {field_name} — {source.name}")

        if dry_run:
            return "converted"

        try:

            result = convert_to_webp(source, quality=user.webp_quality)
            if result is None:
                self.stderr.write(
                    self.style.ERROR(f"  [ERR ] {field_name} — conversion returned None")
                )
                return "error"
            original_name, webp_content = result
            field.save(webp_content.name, webp_content, save=False)
            update_kwargs: dict = {field_name: str(field.name) if field else None}
            if not force:
                update_kwargs[legacy_field_name] = original_name
            User.objects.filter(pk=user.pk).update(**update_kwargs)
            return "converted"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {field_name} — {exc}"))
            return "error"
