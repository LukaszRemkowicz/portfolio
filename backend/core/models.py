import os
import uuid
from io import BytesIO
from typing import Any, cast

from model_utils import FieldTracker
from parler.models import TranslatableModel
from PIL import Image

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from common.utils.image import ImageSpec, convert_to_webp
from core.tasks import process_image_task


class BaseImage(TranslatableModel):
    """Base abstract model for images"""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    path = models.ImageField(
        upload_to="images/",
        verbose_name=_("Image File"),
        help_text=_("The actual image file to be displayed."),
    )
    original_image = models.ImageField(
        upload_to="images/",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image"),
        help_text=_(
            "Original file path before WebP conversion. "
            "Used for rollback via the Admin serve_webp_images toggle. "
            "TODO:Will be removed in future versions."
        ),
    )

    # Translations moved to concrete subclasses because BaseImage is abstract.
    # See AstroImage and ProjectImage.

    thumbnail = models.ImageField(
        upload_to="thumbnails/", blank=True, null=True, editable=False, verbose_name=_("Thumbnail")
    )

    # Track path AND original_image so save() can detect whether _convert_to_webp() preserved
    # the old file as a rollback target (and must not delete it).
    path_tracker = FieldTracker(fields=["path", "original_image"])

    # Subclasses override this to control WebP compression level.
    # AstroImage/ProjectImage keep 90 (photography portfolio); backgrounds/user images
    # use lower values set on those concrete classes.
    webp_quality: int = 90
    max_dimension: int | None = None
    dimension_percentage: int | None = None

    def get_path_spec(self) -> ImageSpec:
        """Default specification provider for the 'path' field."""
        key = "LANDSCAPE" if self.webp_quality >= 90 else "PORTRAIT"
        spec = settings.IMAGE_OPTIMIZATION_SPECS[key]
        return ImageSpec(
            dimension=spec.dimension,
            quality=spec.quality,
            dimension_percentage=self.dimension_percentage,
        )

    def get_image_spec(self, field_name: str) -> ImageSpec:
        """Return the ImageSpec for a given field by dispatching to specialized methods."""
        method_name = f"get_{field_name}_spec"
        if hasattr(self, method_name):
            spec = cast(ImageSpec, getattr(self, method_name)())
            return ImageSpec(
                dimension=spec.dimension,
                quality=spec.quality,
                dimension_percentage=self.dimension_percentage,
            )
        spec = settings.IMAGE_OPTIMIZATION_SPECS.get(
            "DEFAULT", ImageSpec(dimension=1200, quality=75)
        )
        return ImageSpec(
            dimension=spec.dimension,
            quality=spec.quality,
            dimension_percentage=self.dimension_percentage,
        )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        path_changed: bool = self.path_tracker.has_changed("path")

        super().save(*args, **kwargs)

        if (is_new or path_changed) and self.path and not kwargs.get("update_fields"):
            # Trigger background task after save() and inside on_commit to ensure
            # the record exists in the database for the task fetcher.
            transaction.on_commit(
                lambda: process_image_task.delay(
                    self._meta.app_label, self._meta.model_name, str(self.pk)
                )
            )

        if self.pk and path_changed:
            old_path: Any = self.path_tracker.previous("path")
            if old_path:
                storage: Any = self.path.storage
                old_path_str: str = str(old_path)
                # If original_image was freshly set by _convert_to_webp(), the old file is now
                # preserved as the rollback target — do not delete it.
                original_was_set: bool = self.path_tracker.has_changed("original_image") and bool(
                    self.original_image
                )
                if old_path_str and not original_was_set and storage.exists(old_path_str):
                    storage.delete(old_path_str)

    def _convert_to_webp(self) -> bool:
        """Convert from the original source image to WebP using self.get_image_spec().

        Stores the original file path in original_image for rollback purposes.
        No-op if the image is already in WebP format or conversion fails.
        """
        spec = self.get_image_spec("path")
        source = self.get_original_source()
        result: tuple[str, Any] | None = convert_to_webp(
            source,
            quality=spec.quality,
            max_dimension=spec.dimension,
            dimension_percentage=spec.dimension_percentage,
        )
        if result is None:
            return False
        original_name, webp_content = result
        self.original_image = original_name
        self.path.save(webp_content.name, webp_content, save=False)
        return True

    def get_serving_path(self) -> Any:
        """Return the image field to serve based on the serve_webp_images Admin toggle.

        When serve_webp_images=True → serve WebP (self.path).
        When serve_webp_images=False → serve original image if available, else WebP.
        TODO: will be removed in future versions.
        """
        settings_obj: LandingPageSettings | None = LandingPageSettings.get_current()
        if settings_obj and settings_obj.serve_webp_images:
            return self.path
        return self.original_image or self.path

    def get_serving_url(self) -> str:
        """Return the URL string of the image to serve."""
        serving_field: Any = self.get_serving_path()
        if serving_field:
            try:
                return str(serving_field.url)
            except ValueError:
                pass
        return ""

    def get_thumbnail_source(self) -> Any:
        """Prefer the original source image for thumbnail generation when available."""
        return self.get_original_source()

    def get_original_source(self) -> Any:
        """Prefer the active uploaded source file over an older converted original.

        When a new upload is assigned to ``path`` before conversion runs, ``original_image``
        may still point at the previous source asset. In that case we must use the new
        uploaded file from ``path``; otherwise reconversion and thumbnail generation will
        incorrectly reuse stale bytes.
        """
        path_name = str(getattr(self.path, "name", "") or "").lower()
        if self.path and not path_name.endswith(".webp"):
            return self.path
        return self.original_image or self.path

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        return name if name else str(self.id)

    def make_thumbnail(self, image: Any, size: tuple[int, int] | None = None) -> ContentFile:
        """Generate a WebP thumbnail using the configured thumbnail spec."""
        img: Any = Image.open(image)
        # Handle transparency: create a white background if image has alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        spec = settings.IMAGE_OPTIMIZATION_SPECS["THUMBNAIL"]
        target_size = size or (spec.dimension, spec.dimension)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        thumb_io = BytesIO()
        # Use lossless WebP for thumbnail sharpness during visual-quality tuning.
        img.save(thumb_io, "WEBP", lossless=True, method=6)
        original_name = getattr(image, "name", "unknown").split("/")[-1]
        thumbnail_name = "thumb_" + os.path.splitext(original_name)[0] + ".webp"
        return ContentFile(thumb_io.getvalue(), name=thumbnail_name)

    def get_thumbnail_url(self) -> str:
        """Get thumbnail URL or placeholder."""
        if self.thumbnail:
            return self.thumbnail.url  # type: ignore[no-any-return]
        return "/static/images/placeholder.jpg"


class SingletonModel(models.Model):
    """Abstract singleton model to ensure only one instance exists in the database."""

    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Prevent saving more than one instance."""
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError(
                _("A singleton instance of %s already exists.") % self._meta.verbose_name
            )
        super().save(*args, **kwargs)
        # Cleanup: Delete all other instances except the one just saved
        self.__class__.objects.exclude(pk=self.pk).delete()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of the singleton instance via standard delete."""
        return 0, {}


class LandingPageSettings(SingletonModel):
    """Singleton-like model to store global landing page settings."""

    contact_form_enabled = models.BooleanField(default=True, verbose_name=_("Contact Form Enabled"))
    travel_highlights_enabled = models.BooleanField(
        default=True, verbose_name=_("Travel Highlights Enabled")
    )
    programming_enabled = models.BooleanField(
        default=True, verbose_name=_("Programming Section Enabled")
    )
    lastimages_enabled = models.BooleanField(
        default=True, verbose_name=_("Last Images Section Enabled")
    )
    serve_webp_images = models.BooleanField(
        default=False,
        verbose_name=_("Serve WebP Images"),
        help_text=_(
            "When enabled, serves WebP-converted images. "
            "Disable to fall back to the original legacy images for rollback. "
            "Will be removed in future."
        ),
    )
    meteors = models.ForeignKey(
        "astrophotography.MeteorsMainPageConfig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Meteors Configuration"),
        help_text=_("Select the configuration to enable meteors. Leave empty to disable."),
    )

    class Meta:
        verbose_name = _("Landing Page Settings")
        verbose_name_plural = _("Landing Page Settings")

    @classmethod
    def get_current(cls) -> "LandingPageSettings | None":
        """Return the singleton LandingPageSettings instance, or None if not yet created.

        Use this instead of .objects.last() so caching can be added here in future
        without touching any caller.
        """
        return cls.objects.last()

    def __str__(self) -> str:
        return str(_("Landing Page Settings"))
