import os
import uuid
from io import BytesIO
from typing import Any

from model_utils import FieldTracker
from parler.models import TranslatableModel
from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from common.utils.image import convert_to_webp
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
    legacy_path = models.ImageField(
        upload_to="images/",
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Legacy Image Path"),
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

    # Track path AND legacy_path so save() can detect whether _convert_to_webp() preserved
    # the old file as a rollback target (and must not delete it).
    path_tracker = FieldTracker(fields=["path", "legacy_path"])

    # Subclasses override this to control WebP compression level.
    # AstroImage/ProjectImage keep 90 (photography portfolio); backgrounds/user images
    # use lower values set on those concrete classes.
    webp_quality: int = 90
    max_dimension: int | None = None

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
                # If legacy_path was freshly set by _convert_to_webp(), the old file is now
                # preserved as the rollback target — do not delete it.
                legacy_was_set: bool = self.path_tracker.has_changed("legacy_path") and bool(
                    self.legacy_path
                )
                if old_path_str and not legacy_was_set and storage.exists(old_path_str):
                    storage.delete(old_path_str)

    def _convert_to_webp(self) -> bool:
        """Convert the current path image to WebP using self.webp_quality.

        Stores the original file path in legacy_path for rollback purposes.
        No-op if the image is already in WebP format or conversion fails.
        """
        result: tuple[str, Any] | None = convert_to_webp(
            self.path, quality=self.webp_quality, max_dimension=self.max_dimension
        )
        if result is None:
            return False
        original_name, webp_content = result
        self.legacy_path = original_name
        self.path.save(webp_content.name, webp_content, save=False)
        return True

    def get_serving_path(self) -> Any:
        """Return the image field to serve based on the serve_webp_images Admin toggle.

        When serve_webp_images=True → serve WebP (self.path).
        When serve_webp_images=False → serve legacy original if available, else WebP.
        TODO: will be removed in future versions.
        """
        settings_obj: LandingPageSettings | None = LandingPageSettings.get_current()
        if settings_obj and settings_obj.serve_webp_images:
            return self.path
        return self.legacy_path or self.path

    def get_serving_url(self) -> str:
        """Return the URL string of the image to serve."""
        serving_field: Any = self.get_serving_path()
        if serving_field:
            try:
                return str(serving_field.url)
            except ValueError:
                pass
        return ""

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        return name if name else str(self.id)

    def make_thumbnail(self, image: Any, size: tuple[int, int] = (300, 300)) -> ContentFile:
        """Generates a high-compression WebP thumbnail for the image."""
        img: Any = Image.open(image)
        # Handle transparency: create a white background if image has alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        img.thumbnail(size)
        thumb_io = BytesIO()
        # Aggressive WebP settings for thumbnails (Lighthouse target)
        img.save(thumb_io, "WEBP", quality=60)
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
