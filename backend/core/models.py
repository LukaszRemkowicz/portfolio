import logging
import uuid
from typing import Any

from parler.models import TranslatableModel

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.mixins import ImageProcessingModelMixin
from common.types import ImageProcessingOperation, ImageSpec
from common.utils.image import (
    build_webp_thumbnail,
    delete_file_from_storage,
    file_exists_in_storage,
    seeded_image_upload_to,
)
from core.tasks import process_image_task

logger = logging.getLogger(__name__)


class BaseImage(ImageProcessingModelMixin, TranslatableModel):
    """Base abstract model for images"""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    path = models.ImageField(
        upload_to="images/",
        verbose_name=_("Image File"),
        help_text=_(
            "Legacy image field kept during the BaseImage refactor. "
            "TODO: legacy, will be removed in future."
        ),
    )
    original = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "original"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image Source"),
        help_text=_("Uploaded source image for the next BaseImage contract."),
    )
    original_webp = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "webp"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image WebP"),
        help_text=_("Derived WebP image for the next BaseImage contract."),
    )
    original_image = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "original"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image"),
        help_text=_(
            "Legacy original-image field kept during the BaseImage refactor. "
            "Used for rollback via the Admin serve_webp_images toggle. "
            "TODO: legacy, will be removed in future."
        ),
    )

    # Translations moved to concrete subclasses because BaseImage is abstract.
    # See AstroImage and ProjectImage.

    thumbnail = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "thumbnail"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Thumbnail"),
    )

    # Subclasses override this to control WebP compression level.
    # AstroImage/ProjectImage keep 90 (photography portfolio); backgrounds/user images
    # use lower values set on those concrete classes.
    webp_quality: int = 90
    max_dimension: int | None = None
    dimension_percentage: int | None = None

    def get_original_spec(self) -> ImageSpec:
        """Default specification provider for the main source field."""
        key = "LANDSCAPE" if self.webp_quality >= 90 else "PORTRAIT"
        spec = settings.IMAGE_OPTIMIZATION_SPECS[key]
        return ImageSpec(
            dimension=spec.dimension,
            quality=spec.quality,
            dimension_percentage=self.dimension_percentage,
        )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    @property
    def base_upload_dir(self) -> str:
        """Return the model-specific base directory for managed image assets."""
        raise NotImplementedError("Subclasses must define base_upload_dir.")

    def _verify_storage_consistency(
        self, is_new: bool, source_changed: bool, existing_source_name: str
    ) -> None:
        """Ensure the uploaded file was actually saved to storage, with recovery logic."""
        if not (source_changed and existing_source_name and self.original):
            return

        if not file_exists_in_storage(self.original):
            if (
                existing_source_name
                and existing_source_name != str(self.original.name or "")
                and file_exists_in_storage(
                    self.original.field.attr_class(self, self.original.field, existing_source_name)
                )
            ):
                self.original.name = existing_source_name
            else:
                source_name = str(self.original.name or "")
                logger.error(
                    "Image file missing from storage immediately after save",
                    extra={
                        "model": self._meta.label,
                        "pk": str(self.pk),
                        "source_name": source_name,
                        "is_new": is_new,
                        "source_changed": source_changed,
                    },
                )
                if is_new and self.pk:
                    type(self).objects.filter(pk=self.pk).delete()
                raise ValidationError(
                    {
                        "original": _(
                            "The uploaded image file was not saved to " "storage. Please try again."
                        )
                    }
                )

    def _dispatch_image_processing(
        self, is_new: bool, source_changed: bool, update_fields: Any
    ) -> None:
        """Trigger the background celery task to process the image (WebP + thumbnails)."""
        source_field = self.original_field
        if (is_new or source_changed) and source_field and not update_fields:
            logger.info(
                "Dispatching shared image-processing task for BaseImage",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "is_new": is_new,
                    "source_changed": source_changed,
                    "source_name": str(getattr(source_field, "name", "") or ""),
                },
            )
            process_image_task.delay_on_commit(
                self._meta.app_label, self._meta.model_name, str(self.pk)
            )

    def _cleanup_old_files(self, file_names_to_delete: set[str]) -> None:
        """Delete old managed image files after a successful source replacement."""
        if not (self.pk and file_names_to_delete and self.original):
            return

        for file_name in file_names_to_delete:
            delete_file_from_storage(self.original, file_name)

    def _handle_post_save_image_effects(
        self,
        *,
        is_new: bool,
        source_changed: bool,
        existing_source_name: str,
        previous_file_names: set[str],
        update_fields: Any,
    ) -> None:
        """Run image-specific side effects that are only safe after persistence succeeds.

        This method intentionally executes *after* ``super().save()`` so it can work
        from the final stored state instead of the in-memory pre-save state.

        It performs three follow-up steps:

        1. Verify storage consistency for the current ``original`` file. This catches
           cases where the model row was saved but the uploaded file was not actually
           persisted by storage.
        2. Dispatch async image processing when the source really changed. The final
           persisted source name is re-checked here because storage may normalize the
           uploaded filename during save.
        3. Delete stale managed files from the previous state. Cleanup uses the
           pre-save file-name snapshot and only runs when the source genuinely changed.

        Args:
            is_new: Whether the row was being created during this save call.
            source_changed: Whether the source appeared to change before persistence.
            existing_source_name: The stored original-source name from before this save.
            previous_file_names: Managed file names that were attached before save.
            update_fields: The ``update_fields`` value originally passed to ``save()``.
        """
        self._verify_storage_consistency(is_new, source_changed, existing_source_name)
        persisted_source_name = str(getattr(self.original, "name", "") or "")
        effective_source_changed = bool(is_new or persisted_source_name != existing_source_name)
        stale_file_names = previous_file_names if effective_source_changed else set()
        self._dispatch_image_processing(is_new, effective_source_changed, update_fields)
        self._cleanup_old_files(stale_file_names)

    def _synchronize_source_fields(self, previous_source_name: str, is_new: bool) -> None:
        """Update derived-field state from the current original source before save.

        If the source changed, clear stale thumbnail/WebP data.
        If the source itself is a WebP file, mirror it into ``original_webp``.
        """
        source_field = self.original_field
        if not source_field:
            return

        uploaded_name = str(getattr(source_field, "name", "") or "")
        if not uploaded_name:
            return

        source_is_pending_upload = (
            bool(source_field) and getattr(source_field, "_committed", True) is False
        )
        source_updated = is_new or source_is_pending_upload or uploaded_name != previous_source_name

        self.original = source_field
        if uploaded_name.lower().endswith(".webp"):
            self.original_webp = source_field
        elif source_updated:
            self.original_webp = None

        if source_updated:
            self.thumbnail = None

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Persist the model and coordinate source synchronization, processing, and cleanup."""
        is_new = self._state.adding
        previous_source = self.source_tracker.previous(self.original_field_name) if self.pk else ""
        existing_source_name = str(getattr(previous_source, "name", previous_source) or "")
        previous_file_names = {
            file_name
            for file_name in (
                existing_source_name,
                str(getattr(self.original_webp_field, "name", "") or ""),
                str(getattr(self.thumbnail_field, "name", "") or ""),
            )
            if file_name
        }

        if not kwargs.get("update_fields"):
            self._synchronize_source_fields(existing_source_name, is_new)

        current_source_name = str(getattr(self.original, "name", "") or "")
        source_changed = bool(is_new or current_source_name != existing_source_name)

        super().save(*args, **kwargs)
        self._handle_post_save_image_effects(
            is_new=is_new,
            source_changed=source_changed,
            existing_source_name=existing_source_name,
            previous_file_names=previous_file_names,
            update_fields=kwargs.get("update_fields"),
        )

    def get_serving_path(self) -> Any:
        """Return the image field to serve based on the serve_webp_images Admin toggle.

        When serve_webp_images=True -> serve the WebP asset.
        When serve_webp_images=False -> serve the original asset.
        """
        settings_obj: LandingPageSettings | None = LandingPageSettings.get_current()
        if settings_obj and settings_obj.serve_webp_images:
            return self.original_webp_field or self.original_field
        return self.original_field

    def get_serving_url(self) -> str:
        """Return the URL string of the image to serve."""
        serving_field: Any = self.get_serving_path()
        if serving_field:
            try:
                if file_exists_in_storage(serving_field):
                    return str(serving_field.url)
            except (OSError, ValueError):
                logger.warning(
                    "Failed to resolve serving URL for image field %r",
                    getattr(serving_field, "name", None),
                    exc_info=True,
                )
        return ""

    @property
    def original_field(self) -> Any:
        """Return the original asset."""
        return self.original

    @property
    def original_field_name(self) -> str:
        """Return the original field name."""
        return "original"

    @property
    def original_webp_field(self) -> Any:
        """Return the derived WebP asset."""
        return self.original_webp

    @property
    def original_webp_field_name(self) -> str:
        """Return the derived WebP field name."""
        return "original_webp"

    @property
    def thumbnail_field(self) -> Any:
        """Return the thumbnail asset."""
        return self.thumbnail

    @property
    def thumbnail_field_name(self) -> str:
        """Return the thumbnail field name."""
        return "thumbnail"

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        return name if name else str(self.id)

    def make_thumbnail(self, image: Any, size: tuple[int, int] | None = None) -> ContentFile:
        """Generate a WebP thumbnail using the configured thumbnail spec."""
        spec = settings.IMAGE_OPTIMIZATION_SPECS["THUMBNAIL"]
        target_size = size or (spec.dimension, spec.dimension)
        return build_webp_thumbnail(image, size=target_size)

    def get_thumbnail_url(self) -> str | None:
        """Get thumbnail URL only when the thumbnail file exists."""
        if self.thumbnail:
            try:
                if file_exists_in_storage(self.thumbnail):
                    return self.thumbnail.url  # type: ignore[no-any-return]
            except (OSError, ValueError):
                return None
        return None

    def get_image_processing_operations(
        self, changed_field_names: list[str] | None = None
    ) -> list[ImageProcessingOperation]:
        """Describe the image-processing workflow for this model instance."""
        return [
            ImageProcessingOperation(
                field_name=self.original_field_name,
                source_image=self.original_field,
                webp_field_name=self.original_webp_field_name,
                spec=self.get_original_spec(),
                original_field_name=self.original_field_name,
                thumbnail_field_name=self.thumbnail_field_name,
                thumbnail_source_image=self.original_field,
                thumbnail_generator=self.make_thumbnail,
            )
        ]


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
    shop_enabled = models.BooleanField(default=False, verbose_name=_("Shop Section Enabled"))
    serve_webp_images = models.BooleanField(
        default=False,
        verbose_name=_("Serve WebP Images"),
        help_text=_(
            "When enabled, serves WebP-converted images. "
            "Disable to fall back to the original legacy images for rollback. "
            "Will be removed in future."
        ),
    )
    latest_filters = models.ManyToManyField(
        "astrophotography.Tag",
        blank=True,
        verbose_name=_("Latest Image Filters"),
        help_text=_("Tags that will appear as filters in the 'Latest images' section."),
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
