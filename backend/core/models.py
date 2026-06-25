import logging
import uuid
from typing import Any, ClassVar

from parler.models import TranslatableModel

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.utils.translation import gettext_lazy as _

from common.types import ImageVariantSource, ImageVariantSpec
from common.utils.image import (
    IMAGE_FORMAT,
    delete_file_from_storage,
    file_exists_in_storage,
    seeded_image_upload_to,
)
from core.mixins import ImageVariantModelMixin
from core.tasks import process_image_task

logger = logging.getLogger(__name__)


class ImageVariantQuerySet(models.QuerySet):
    """QuerySet that keeps file cleanup consistent with instance deletion."""

    def delete(self) -> tuple[int, dict[str, int]]:
        for variant in self.iterator():
            variant.delete_file()
        return super().delete()


class ImageVariant(models.Model):
    """A generated responsive image file owned by an image model instance."""

    objects = ImageVariantQuerySet.as_manager()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
        help_text=_("Stable identifier of this generated image variant row."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=_("Concrete image model that owns this variant."),
    )
    object_id = models.CharField(
        max_length=64,
        help_text=_("Primary key of the concrete image object that owns this variant."),
    )
    image = GenericForeignKey("content_type", "object_id")
    file = models.ImageField(
        blank=True,
        editable=False,
        upload_to="",
        verbose_name=_("File"),
        help_text=_("Generated WebP file stored for this variant."),
    )
    role = models.CharField(
        max_length=32,
        verbose_name=_("Role"),
        help_text=_("Frontend display role for this variant, such as card, detail, or hero."),
    )
    width = models.PositiveIntegerField(
        verbose_name=_("Width"),
        help_text=_("Generated image width in pixels."),
    )
    height = models.PositiveIntegerField(
        verbose_name=_("Height"),
        help_text=_("Generated image height in pixels."),
    )
    mime_type = models.CharField(
        max_length=64,
        default=IMAGE_FORMAT.mime_type,
        verbose_name=_("MIME Type"),
        help_text=_("MIME type of the generated variant file."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When this variant row was first created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("When this variant row was last updated."),
    )

    class Meta:
        ordering = ["role", "width"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "role", "width"],
                name="core_imagevariant_unique_owner_role_width",
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["role", "width"]),
        ]

    def __str__(self) -> str:
        return f"{self.role} {self.width}w for {self.content_type_id}:{self.object_id}"

    def delete_file(self) -> None:
        """Delete the stored variant file without saving this row."""
        if self.file:
            self.file.delete(save=False)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Delete the stored variant file together with this row."""
        self.delete_file()
        return super().delete(*args, **kwargs)


class BaseImage(ImageVariantModelMixin, TranslatableModel):
    """Base abstract model for images"""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    original = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "original"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image Source"),
        help_text=_("Uploaded source image for the next BaseImage contract."),
    )
    # Translations moved to concrete subclasses because BaseImage is abstract.
    # See AstroImage and ProjectImage.

    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
    )

    image_variant_specs: ClassVar[tuple[ImageVariantSpec, ...]] = ()

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
        source_field = self.original
        if not (source_changed and existing_source_name and source_field):
            return

        if not file_exists_in_storage(source_field):
            if (
                existing_source_name
                and existing_source_name != str(source_field.name or "")
                and file_exists_in_storage(
                    source_field.field.attr_class(  # type: ignore[attr-defined]
                        self, source_field.field, existing_source_name
                    )
                )
            ):
                source_field.name = existing_source_name
            else:
                source_name = str(source_field.name or "")
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
        """Trigger the background celery task to process thumbnails and variants."""
        source_field = self.original
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
                self._meta.app_label,
                self._meta.model_name,
                str(self.pk),
                [source_field.field.name],
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

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Persist the model and coordinate source synchronization, processing, and cleanup."""
        is_new = self._state.adding
        source_field_name = self.original.field.name
        previous_source = self.source_tracker.previous(source_field_name) if self.pk else ""
        existing_source_name = str(getattr(previous_source, "name", previous_source) or "")
        previous_file_names = {existing_source_name} if existing_source_name else set()

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

    def get_original_image_url(self) -> str | None:
        """Return the original source URL when it exists in storage."""
        if self.original and file_exists_in_storage(self.original):
            return str(self.original.url)
        return None

    def get_image_url(self, role: str, width: int) -> str | None:
        """Return the generated variant URL or fall back to the original source URL."""
        variant_url: str | None = self.get_variant_url(role, width)
        if variant_url:
            return variant_url

        original_url: str | None = self.get_original_image_url()
        if original_url:
            logger.warning(
                "Falling back to original source image because variant is missing",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "role": role,
                    "source_name": str(getattr(self.original, "name", "") or ""),
                },
            )
            return original_url
        logger.error(
            "Image variant is missing and original source image is unavailable",
            extra={
                "model": self._meta.label,
                "pk": str(self.pk),
                "role": role,
                "width": width,
                "source_name": str(getattr(self.original, "name", "") or ""),
            },
        )
        return None

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        return name if name else str(self.id)

    def get_original_image(self) -> ImageFieldFile | None:
        """Return the stored image file that should seed generated variants."""
        if file_exists_in_storage(self.original):
            return self.original  # type: ignore[no-any-return]  # Django ImageField descriptor.
        if self.original:
            logger.error(
                "Original image file is missing from storage",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "source_name": str(getattr(self.original, "name", "") or ""),
                },
            )
        return None

    def get_image_variant_sources(
        self, _changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        """Return the single original image source used by BaseImage variants."""
        return [
            ImageVariantSource(
                field_name=self.original.field.name,
                source_image=self.get_original_image(),
                upload_dir=self.base_upload_dir,
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
