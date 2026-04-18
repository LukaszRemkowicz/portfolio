"""Management command to batch-convert existing images to WebP format.

Usage:
    python manage.py convert_images_to_webp          # Convert all images
    python manage.py convert_images_to_webp --dry-run # Preview without changes

Safe to re-run: images that are already WebP or already have a derived WebP field are skipped.
After running, flip LandingPageSettings.serve_webp_images = True in Django Admin.
"""

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand

from astrophotography.models import AstroImage, MainPageBackgroundImage
from common.types import ImageSpec
from common.utils.image import convert_to_webp
from programming.models import ProjectImage
from users.models import User


class Command(BaseCommand):
    """Batch-convert stored images to WebP using each model's image settings."""

    help = "Convert existing images to WebP and populate derived WebP fields."

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
                "Re-convert already-converted images from their original source field "
                "using the model's current webp_quality. Use after changing quality settings."
            ),
        )
        parser.add_argument(
            "--object-id",
            type=str,
            help=(
                "Convert only a single BaseImage object by primary key. "
                "Applies to AstroImage, MainPageBackgroundImage, and ProjectImage."
            ),
        )
        parser.add_argument(
            "--object-ids",
            nargs="+",
            help=(
                "Convert only the listed BaseImage objects by primary key. "
                "Applies to AstroImage, MainPageBackgroundImage, and ProjectImage."
            ),
        )
        parser.add_argument(
            "--dimension-percentage",
            type=int,
            help=(
                "Scale image width and height by this percentage of the original size. "
                "Overrides model max_dimension for this command run."
            ),
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]
        object_id: str | None = options.get("object_id")
        object_ids: list[str] | None = options.get("object_ids")
        dimension_percentage: int | None = options.get("dimension_percentage")

        if object_id and object_ids:
            self.stderr.write(self.style.ERROR("Use either --object-id or --object-ids, not both."))
            return
        if dimension_percentage is not None and not 1 <= dimension_percentage <= 100:
            self.stderr.write(self.style.ERROR("--dimension-percentage must be between 1 and 100."))
            return

        target_ids = [object_id] if object_id else object_ids

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made.\n"))
        if force:
            self.stdout.write(self.style.WARNING("FORCE MODE — re-converting from originals.\n"))
        if target_ids:
            joined_ids = ", ".join(target_ids)
            self.stdout.write(self.style.WARNING(f"OBJECT FILTER — only {joined_ids}\n"))
        if dimension_percentage is not None:
            self.stdout.write(
                self.style.WARNING(
                    f"DIMENSION PERCENTAGE OVERRIDE — {dimension_percentage}% of original size\n"
                )
            )

        total_converted = 0
        total_skipped = 0
        total_errors = 0

        # ---------- BaseImage subclasses ----------
        conv, skip, err = self._handle_base_images(dry_run, force, target_ids, dimension_percentage)
        total_converted += conv
        total_skipped += skip
        total_errors += err

        # ---------- User image fields ----------
        if target_ids is None:
            conv, skip, err = self._handle_user_images(dry_run, force, dimension_percentage)
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

    def _handle_base_images(
        self,
        dry_run: bool,
        force: bool,
        object_ids: list[str] | None = None,
        dimension_percentage: int | None = None,
    ) -> tuple[int, int, int]:
        """Process all BaseImage subclasses. Returns (converted, skipped, errors)."""
        conv, skip, err = 0, 0, 0
        base_image_models = [
            ("AstroImage", AstroImage.objects.all()),
            ("MainPageBackgroundImage", MainPageBackgroundImage.objects.all()),
            ("ProjectImage", ProjectImage.objects.all()),
        ]

        matched_any = False
        for model_name, queryset in base_image_models:
            if object_ids is not None:
                queryset = queryset.filter(pk__in=object_ids)
            count = queryset.count()
            self.stdout.write(f"\n{model_name} ({count} records):")
            if count > 0:
                matched_any = True

            for obj in queryset:
                result = self._convert_base_image(obj, dry_run, force, dimension_percentage)
                if result == "converted":
                    conv += 1
                elif result == "skipped":
                    skip += 1
                else:
                    err += 1

        if object_ids is not None and not matched_any:
            self.stderr.write(
                self.style.ERROR(
                    f"No BaseImage objects found for requested ids: {', '.join(object_ids)}"
                )
            )
            err += 1
        return conv, skip, err

    def _handle_user_images(
        self, dry_run: bool, force: bool, dimension_percentage: int | None = None
    ) -> tuple[int, int, int]:
        """Process User model image fields. Returns (converted, skipped, errors)."""
        conv, skip, err = 0, 0, 0
        user = User.get_user()
        if not user:
            return 0, 0, 0

        self.stdout.write("\nUser images:")
        for field_name, webp_field_name in [
            ("avatar", "avatar_webp"),
            ("about_me_image", "about_me_image_webp"),
            ("about_me_image2", "about_me_image2_webp"),
        ]:
            result = self._convert_user_field(
                user,
                field_name,
                webp_field_name,
                dry_run,
                force,
                dimension_percentage,
            )
            if result == "converted":
                conv += 1
            elif result == "skipped":
                skip += 1
            else:
                err += 1
        return conv, skip, err

    def _convert_base_image(
        self,
        obj,
        dry_run: bool,
        force: bool = False,
        dimension_percentage: int | None = None,
    ) -> str:
        """Convert a BaseImage subclass instance. Returns 'converted', 'skipped', or 'error'."""
        name = str(obj)
        if not obj.path:
            self.stdout.write(f"  [SKIP] {name} — no path")
            return "skipped"

        current_name = str(obj.path.name)

        if current_name.lower().endswith(".webp") and not force:
            self.stdout.write(f"  [SKIP] {name} — already WebP")
            return "skipped"

        if obj.original_image and not force:
            self.stdout.write(f"  [SKIP] {name} — already has original_image")
            return "skipped"

        # In force mode, re-convert from the original (original_image) at the new quality.
        # If no original_image exists (first-time conversion), use obj.path as source.
        source = obj.original_image if (force and obj.original_image) else obj.path
        label = "RECONV" if (force and obj.original_image) else "CONV"
        self.stdout.write(f"  [{label}] {name} — {source.name}")

        if dry_run:
            return "converted"

        try:
            spec: ImageSpec = obj.get_image_spec("path")
            result = convert_to_webp(
                source,
                quality=spec.quality,
                max_dimension=spec.dimension,
                dimension_percentage=dimension_percentage or spec.dimension_percentage,
            )
            if result is None:
                self.stderr.write(self.style.ERROR(f"  [ERR ] {name} — conversion returned None"))
                return "error"
            original_name, webp_content = result
            # Save the new WebP, overwriting obj.path
            obj.path.save(webp_content.name, webp_content, save=False)
            if obj.path:
                thumb_source = source if source else obj.get_thumbnail_source()
                thumb_content: ContentFile = obj.make_thumbnail(thumb_source)
                obj.thumbnail.save(thumb_content.name, thumb_content, save=False)
            update_kwargs = {
                "path": str(obj.path.name) if obj.path else None,
                "thumbnail": str(obj.thumbnail.name) if obj.thumbnail else None,
            }
            # Only set original_image on first conversion (not on force re-conversion)
            if not force:
                update_kwargs["original_image"] = original_name
            type(obj).objects.filter(pk=obj.pk).update(**update_kwargs)
            return "converted"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {name} — {exc}"))
            return "error"

    def _convert_user_field(
        self,
        user: User,
        field_name: str,
        webp_field_name: str,
        dry_run: bool,
        force: bool = False,
        dimension_percentage: int | None = None,
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

        webp_field = getattr(user, webp_field_name)
        if webp_field and not force:
            self.stdout.write(f"  [SKIP] {field_name} — already has derived WebP")
            return "skipped"

        source = field
        label = "RECONV" if force else "CONV"
        self.stdout.write(f"  [{label}] {field_name} — {source.name}")

        if dry_run:
            return "converted"

        try:
            # Determine which spec method to call based on the field name
            spec_method_name = "get_avatar_spec" if field_name == "avatar" else "get_portrait_spec"
            spec: ImageSpec = getattr(user, spec_method_name)()

            result = convert_to_webp(
                source,
                quality=spec.quality,
                max_dimension=spec.dimension,
                dimension_percentage=dimension_percentage or spec.dimension_percentage,
            )
            if result is None:
                self.stderr.write(
                    self.style.ERROR(f"  [ERR ] {field_name} — conversion returned None")
                )
                return "error"
            _, webp_content = result
            webp_field.save(webp_content.name, webp_content, save=False)
            update_kwargs: dict = {webp_field_name: str(webp_field.name) if webp_field else None}
            User.objects.filter(pk=user.pk).update(**update_kwargs)
            return "converted"
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  [ERR ] {field_name} — {exc}"))
            return "error"
