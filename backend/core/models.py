import logging
import uuid
from typing import Any, ClassVar

from parler.models import TranslatableModel

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import ImageFieldFile
from django.utils.translation import gettext_lazy as _

from common.mixins import ImageProcessingModelMixin
from common.types import ImageProcessingOperation, ImageSpec, ImageVariantSpec
from common.utils.image import (
    IMAGE_FORMAT,
    build_image_thumbnail,
    build_image_with_given_width,
    delete_file_from_storage,
    file_exists_in_storage,
    has_output_image_extension,
    seeded_image_upload_to,
)
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
    object_id = models.UUIDField(
        help_text=_("Primary key of the concrete image object that owns this variant.")
    )
    image = GenericForeignKey("content_type", "object_id")
    file = models.FileField(
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


class BaseImage(ImageProcessingModelMixin, TranslatableModel):
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
    original_webp = models.ImageField(
        upload_to=seeded_image_upload_to("base_upload_dir", "webp"),
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Original Image WebP"),
        help_text=_(
            "TODO: Derived WebP image kept during the ImageVariant rollout. "
            "Remove after generated variants are the public serving path."
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
        help_text=_(
            "TODO: Legacy thumbnail field kept during the ImageVariant rollout. "
            "Remove after thumbnail variants are the public serving path."
        ),
    )
    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
    )

    # Subclasses override this to control WebP compression level.
    # AstroImage/ProjectImage keep 90 (photography portfolio); backgrounds/user images
    # use lower values set on those concrete classes.
    webp_quality: int = 90
    max_dimension: int | None = None
    dimension_percentage: int | None = None
    image_variant_specs: ClassVar[tuple[ImageVariantSpec, ...]] = ()

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
                self._meta.app_label,
                self._meta.model_name,
                str(self.pk),
                [self.original_field_name],
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
        if has_output_image_extension(uploaded_name):
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
    def original_field(self) -> ImageFieldFile | None:
        """Return the original asset."""
        original: ImageFieldFile | None = self.original
        return original

    @property
    def original_field_name(self) -> str:
        """Return the original field name."""
        return "original"

    @property
    def original_webp_field(self) -> ImageFieldFile | None:
        """Return the derived WebP asset."""
        original_webp: ImageFieldFile | None = self.original_webp
        return original_webp

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
        return build_image_thumbnail(image, size=target_size)

    def get_image_variant_specs(self) -> tuple[ImageVariantSpec, ...]:
        """Return responsive variant specs for this image model."""
        return self.image_variant_specs

    def generate_image_variants_or_none(
        self, *, force: bool = False
    ) -> models.QuerySet[ImageVariant] | None:
        """Synchronize responsive variant files with the current model specs.

        Default sync is incremental: remove stale variant rows and generate only
        missing role/width files. ``force=True`` deletes all existing variants and
        rebuilds every candidate supported by the current source image.
        """
        specs: tuple[ImageVariantSpec, ...] = self.get_image_variant_specs()
        source: Any = self.image_variant_source_field
        if not specs or not source:
            if not self.pk:
                return None
            stale_variants = self.variants.all()
            if stale_variants.exists():
                stale_variants.delete()
                empty_variants: models.QuerySet[ImageVariant] = self.variants.none()
                return empty_variants
            return None

        if force:
            self.variants.all().delete()
            return self._generate_image_variants_for_specs(specs)

        variants_to_generate: tuple[ImageVariantSpec, ...]
        variants_to_delete: models.QuerySet[ImageVariant]
        variants_to_generate, variants_to_delete = self._get_image_variant_sync_plan(specs)
        if not variants_to_generate and not variants_to_delete.exists():
            return None

        variants_to_delete.delete()
        return self._generate_image_variants_for_specs(variants_to_generate)

    def _get_image_variant_sync_plan(
        self, specs: tuple[ImageVariantSpec, ...]
    ) -> tuple[tuple[ImageVariantSpec, ...], "models.QuerySet[ImageVariant]"]:
        """Plan variant sync against specs supported by the current source image.

        Returns role/width candidates missing from valid existing rows, plus
        existing rows whose role/width is no longer expected or whose file is empty.
        """
        expected_specs = self._get_expected_image_variant_specs(specs)
        expected_keys = {(spec.role, width) for spec in expected_specs for width in spec.widths}
        existing_variants = list(self.variants.all())
        valid_existing_keys = {
            (variant.role, variant.width)
            for variant in existing_variants
            if (variant.role, variant.width) in expected_keys and variant.file.name
        }
        variant_ids_to_delete = [
            variant.pk
            for variant in existing_variants
            if (variant.role, variant.width) not in expected_keys or not variant.file.name
        ]
        missing_keys = expected_keys - valid_existing_keys
        variants_to_generate = tuple(
            ImageVariantSpec(
                role=spec.role,
                widths=tuple(width for width in spec.widths if (spec.role, width) in missing_keys),
                quality=spec.quality,
                label=spec.label,
            )
            for spec in expected_specs
        )
        variants_to_delete: models.QuerySet[ImageVariant] = self.variants.filter(
            pk__in=variant_ids_to_delete
        )
        return (
            tuple(spec for spec in variants_to_generate if spec.widths),
            variants_to_delete,
        )

    def _get_expected_image_variant_specs(
        self, specs: tuple[ImageVariantSpec, ...]
    ) -> tuple[ImageVariantSpec, ...]:
        """Return configured variant specs that the current source can generate."""
        source_width = self._get_source_width()
        if source_width is None:
            return ()
        return tuple(
            ImageVariantSpec(
                role=spec.role,
                widths=tuple(width for width in spec.widths if width <= source_width),
                quality=spec.quality,
                label=spec.label,
            )
            for spec in specs
        )

    def _generate_image_variants_for_specs(
        self, specs: tuple[ImageVariantSpec, ...]
    ) -> models.QuerySet[ImageVariant]:
        """Create missing variant files and rows for explicit role/width specs.

        Each generated project-format file is saved through ``ImageVariant.file``, which also
        persists the variant row. Returns a queryset filtered to rows created by
        this call; invalid or too-large source images simply produce no row.
        """
        generated_variant_ids: list[uuid.UUID] = []
        source: Any = self.image_variant_source_field
        if not source:
            empty_variants: models.QuerySet[ImageVariant] = self.variants.none()
            return empty_variants

        for spec in specs:
            for width in spec.widths:
                with source.open("rb") as opened_source:
                    result: tuple[ContentFile, int, int] | None = build_image_with_given_width(
                        opened_source,
                        width=width,
                        quality=spec.quality,
                        filename_prefix=f"{spec.role}_{width}_",
                    )

                if result is None:
                    continue

                content, generated_width, generated_height = result
                variant: ImageVariant = ImageVariant(
                    image=self,
                    role=spec.role,
                    width=generated_width,
                    height=generated_height,
                    mime_type=IMAGE_FORMAT.mime_type,
                )
                variant.file.save(
                    f"{self.base_upload_dir}/{spec.role}/{content.name}",
                    content,
                )
                generated_variant_ids.append(variant.pk)

        generated_variants: models.QuerySet[ImageVariant] = self.variants.filter(
            pk__in=generated_variant_ids
        )
        return generated_variants

    def _get_source_width(self) -> int | None:
        source = self.image_variant_source_field
        if not source:
            return None

        return source.width

    @property
    def image_variant_source_field(self) -> ImageFieldFile | None:
        """Return the stored image file that should seed generated variants.

        The canonical upload source is preferred. During the ImageVariant rollout,
        production also has legacy rows where ``original`` still points at a removed
        PNG while ``original_webp`` is the surviving generated file that has been
        served publicly. Variant backfill must use that surviving file instead of
        treating the row as unrecoverable.
        """
        if file_exists_in_storage(self.original_field):
            return self.original_field
        if file_exists_in_storage(self.original_webp_field):
            return self.original_webp_field
        return self.original_field

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
