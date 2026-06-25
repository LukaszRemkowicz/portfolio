import logging
import uuid
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.types import ImageVariantSource, ImageVariantSpec, ViewportWidths
from common.utils.image import file_exists_in_storage, get_available_image_url
from core.mixins import ImageVariantModelMixin
from core.models import ImageVariant, SingletonModel
from core.tasks import process_image_task
from translation.mixins import AutomatedTranslationModelMixin

logger = logging.getLogger(__name__)


class ShopProduct(ImageVariantModelMixin, AutomatedTranslationModelMixin, TranslatableModel):
    """
    A product or item sold in the shop section of the portfolio.

    Provides translatable title and description, shop-specific metadata
    (price, currency, external_url, etc.), and optionally links to an
    existing AstroImage for its visual assets.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    # Translation trigger fields
    translation_service_method = "translate_shop_product"
    translation_trigger_fields = ["title", "description"]
    image_variant_specs = (
        ImageVariantSpec(
            role="original_format",
            viewport_widths=ViewportWidths.fixed(560),
            quality=90,
            label="Shop product display candidate",
        ),
        ImageVariantSpec(
            role="thumbnail",
            viewport_widths=ViewportWidths.fixed(560),
            quality=90,
            label="Shop product card thumbnail candidate",
        ),
    )
    image_tracker = FieldTracker(fields=["image", "image_cropped"])

    image = models.ForeignKey(
        "astrophotography.AstroImage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Image"),
        help_text=_("Select an existing gallery image for this product."),
    )

    # --- Translations ---
    translations = TranslatedFields(
        title=models.CharField(
            max_length=255,
            verbose_name=_("Title"),
            help_text=_("Product title as displayed in the shop."),
        ),
        description=CKEditor5Field(
            verbose_name=_("Description"),
            help_text=_("Short product description."),
            config_name="default",
            blank=True,
        ),
    )

    # --- Shop metadata ---
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Price"),
        help_text=_("Leave blank if price is displayed on the external site."),
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        verbose_name=_("Currency"),
        help_text=_("ISO 4217 currency code, e.g. USD, EUR, PLN."),
    )
    image_cropped = models.ImageField(
        upload_to="shop/products/cropped/",
        null=True,
        blank=True,
        db_column="thumbnail_cropped",
        verbose_name=_("Image (Cropped)"),
        help_text=_(
            "Crop of the selected original image. Used as the source for generated shop variants."
        ),
    )
    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
    )

    external_url = models.URLField(
        blank=True,
        verbose_name=_("External URL"),
        help_text=_("Link to the product on an external shop or marketplace."),
    )
    thumbnail_url = models.URLField(
        blank=True,
        default="",
        verbose_name=_("Thumbnail URL"),
        help_text=_(
            "External CDN URL for the product thumbnail image. "
            "Used as a fallback when no local image has been uploaded."
        ),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Only active products are shown in the public shop."),
    )

    objects = TranslatableManager()  # type: ignore[django-manager-missing]

    class Meta:
        verbose_name = _("Shop Product")
        verbose_name_plural = _("Shop Products")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return the translated product title when available, otherwise fall back to the UUID."""
        # BaseImage.__str__ uses "name" translation; our translatable field is "title"
        title = self.safe_translation_getter("title", any_language=True)
        return title if title else str(self.id)

    def _get_product_image_source(self) -> Any:
        """Return the manual crop used for product public rendering."""
        return getattr(self, "image_cropped", None)

    def _get_product_variant_source(self) -> Any:
        """Return the preferred source image for generated product variants."""
        source_image = self._get_product_image_source()
        if source_image:
            return source_image

        astro_image = getattr(self, "image", None)
        if astro_image is not None:
            return getattr(astro_image, "original", None)

        return None

    def get_image_url(self, role: str, width: int) -> str | None:
        """Return the best available product image URL following crop and AstroImage fallbacks."""
        variant_url: str | None = self.get_variant_url(role, width)
        if variant_url:
            return variant_url

        source_image = self._get_product_image_source()
        cropped_url = get_available_image_url(source_image)
        if cropped_url:
            logger.info(
                "Falling back to product cropped source image because variant is missing",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "role": role,
                    "width": width,
                    "source_name": str(getattr(source_image, "name", "") or ""),
                },
            )
            return cropped_url

        astro_image = getattr(self, "image", None)
        if astro_image is not None:
            astro_thumbnail_url = astro_image.get_image_url("thumbnail", width)
            if astro_thumbnail_url:
                logger.info(
                    "Falling back to linked AstroImage thumbnail variant"
                    " because product crop is unavailable",
                    extra={
                        "model": self._meta.label,
                        "pk": str(self.pk),
                        "role": role,
                        "width": width,
                        "source_pk": str(astro_image.pk),
                    },
                )
                return str(astro_thumbnail_url)

        logger.error(
            "Image variant is missing for requested product role and width",
            extra={
                "model": self._meta.label,
                "pk": str(self.pk),
                "role": role,
                "width": width,
            },
        )
        return None

    # ------------------------------------------------------------------
    # Save logic
    # ------------------------------------------------------------------

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Clear stale manual crops and trigger translations when relevant."""
        image_changed: bool = self.image_tracker.has_changed("image")
        crop_changed: bool = self.image_tracker.has_changed("image_cropped")
        update_fields = kwargs.get("update_fields")
        image_update_fields = {"image", "image_cropped"}
        should_process_images = bool(image_changed or crop_changed) and (
            update_fields is None or bool(image_update_fields.intersection(set(update_fields)))
        )

        if image_changed and not crop_changed:
            self.image_cropped = None
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"image_cropped"}

        super().save(*args, **kwargs)
        if should_process_images:
            process_image_task.delay_on_commit(
                self._meta.app_label,
                self._meta.model_name,
                self.pk,
                sorted(image_update_fields),
            )
        if not update_fields or any(
            field in update_fields for field in self.translation_trigger_fields
        ):
            self.trigger_translations()

    def get_image_variant_sources(
        self, _changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        """Return the image source that should produce product variants."""
        source_image = self._get_product_variant_source()
        field_name = "image_cropped" if self._get_product_image_source() else "image"

        return [
            ImageVariantSource(
                field_name=field_name,
                source_image=source_image,
                upload_dir="shop/products/cropped",
            )
        ]


class ShopSettings(
    ImageVariantModelMixin,
    AutomatedTranslationModelMixin,
    TranslatableModel,
    SingletonModel,
):
    """
    Singleton model to store global settings for the shop page.
    """

    image_variant_specs = (
        ImageVariantSpec(
            role="original_format",
            viewport_widths=ViewportWidths.fixed(1920),
            quality=90,
            label="Shop background original-format display candidate",
        ),
        ImageVariantSpec(
            role="background",
            viewport_widths=ViewportWidths.fixed(1920),
            quality=90,
            label="Shop background display candidate",
        ),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    translation_service_method = "translate_shop_settings"
    translation_trigger_fields = ["title", "description"]

    image_tracker = FieldTracker(fields=["image", "image_cropped"])

    image = models.ImageField(
        upload_to="shop/backgrounds/",
        verbose_name=_("Background Source"),
        help_text=_("The source background image used for the shop page."),
    )

    image_cropped = models.ImageField(
        upload_to="shop/backgrounds/",
        null=True,
        blank=True,
        verbose_name=_("Background Cropped"),
        help_text=_("Cropped background image managed by the admin image cropper."),
    )
    variants = GenericRelation(
        ImageVariant,
        content_type_field="content_type",
        object_id_field="object_id",
    )

    translations = TranslatedFields(
        title=models.CharField(
            max_length=255,
            verbose_name=_("Shop Title"),
            help_text=_("Main title displayed on the shop page."),
        ),
        description=CKEditor5Field(
            verbose_name=_("Shop Description"),
            help_text=_("Text block displayed below the title."),
            config_name="default",
            blank=True,
        ),
    )

    objects = TranslatableManager()  # type: ignore[django-manager-missing,misc]

    class Meta:
        verbose_name = _("Shop Settings")
        verbose_name_plural = _("Shop Settings")

    @classmethod
    def get_current(cls) -> "ShopSettings | None":
        """Return the singleton shop settings instance, or ``None`` when not created yet."""
        return cls.objects.last()

    @classmethod
    def get_or_create_current(cls, **create_kwargs: Any) -> tuple["ShopSettings", bool]:
        """Return the singleton shop settings instance or create it with optional defaults."""
        current = cls.get_current()
        if current is not None:
            return current, False
        return cls.objects.create(**create_kwargs), True

    def __str__(self) -> str:
        """Return the translated shop title when available, otherwise a stable singleton label."""
        title = self.safe_translation_getter("title", any_language=True)
        return title if title else str(_("Shop Settings"))

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        1. Reset `image_cropped` when the source background changes independently.
        2. Schedule the derived-image task when a source image changes on a normal save.
        3. Delegate persistence to the parent model.
        4. Trigger automated translations only for translation-field saves.
        """
        source_changed: bool = self.image_tracker.has_changed("image")
        cropped_changed: bool = self.image_tracker.has_changed("image_cropped")
        update_fields = kwargs.get("update_fields")
        image_update_fields = {"image", "image_cropped"}
        should_process_images = bool(source_changed or cropped_changed) and (
            update_fields is None or bool(image_update_fields.intersection(set(update_fields)))
        )

        if source_changed and not cropped_changed:
            self.image_cropped = None
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"image_cropped"}

        super().save(*args, **kwargs)

        if should_process_images:
            process_image_task.delay_on_commit(
                self._meta.app_label,
                self._meta.model_name,
                self.pk,
                sorted(image_update_fields),
            )

        if not update_fields or any(
            field in update_fields for field in self.translation_trigger_fields
        ):
            self.trigger_translations()

    def get_background_image_url(self) -> str | None:
        """Return the generated background URL."""
        background_spec = next(
            spec for spec in self.image_variant_specs if spec.role == "background"
        )
        width = background_spec.viewport_widths.as_tuple()[-1]
        return self.get_image_url("background", width)

    def get_image_url(self, role: str, width: int) -> str | None:
        """Return the generated variant URL or fall back to the background source URL."""
        variant_url: str | None = self.get_variant_url(role, width)
        if variant_url:
            return variant_url

        source_image = getattr(self, "image_cropped", None) or getattr(self, "image", None)
        if source_image and file_exists_in_storage(source_image):
            logger.warning(
                "Falling back to background source image because variant is missing",
                extra={
                    "model": self._meta.label,
                    "pk": str(self.pk),
                    "role": role,
                    "source_name": str(getattr(source_image, "name", "") or ""),
                },
            )
            return str(source_image.url)
        logger.error(
            "Image variant is missing and background source image is unavailable",
            extra={
                "model": self._meta.label,
                "pk": str(self.pk),
                "role": role,
                "width": width,
                "source_name": str(getattr(source_image, "name", "") or ""),
            },
        )
        return None

    def get_image_variant_sources(
        self, _changed_field_names: list[str] | None = None
    ) -> list[ImageVariantSource]:
        source_image = getattr(self, "image_cropped", None) or getattr(self, "image", None)
        return [
            ImageVariantSource(
                field_name="image",
                source_image=source_image,
                upload_dir="shop/backgrounds",
            )
        ]
