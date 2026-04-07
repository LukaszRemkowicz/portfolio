# backend/shop/models.py
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatedFields

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.utils.image import ImageSpec
from core.models import BaseImage
from translation.mixins import AutomatedTranslationModelMixin


class ShopProduct(AutomatedTranslationModelMixin, BaseImage):
    """
    A product or item sold in the shop section of the portfolio.

    Inherits from BaseImage which provides:
    - UUID primary key
    - path (source ImageField), original_image (pre-WebP rollback), thumbnail
    - path_tracker, _convert_to_webp(), make_thumbnail()
    - Automatic dispatch of core.process_image_task on path change
    - get_serving_url(), get_thumbnail_url()

    Extends with:
    - path_cropped: admin cropper target field
    - Translatable title and description
    - Shop-specific metadata (price, currency, external_url, is_active, order)
    """

    # Translation trigger fields
    translation_service_method = "translate_shop_product"
    translation_trigger_fields = ["title", "description"]

    # Use THUMBNAIL-level quality for product images (good fidelity, smaller file)
    webp_quality: int = 85

    # Override the path_tracker to also detect changes on path_cropped
    path_tracker = FieldTracker(fields=["path", "original_image", "path_cropped"])

    # Override BaseImage.path to keep shop images in their own directory
    path = models.ImageField(
        upload_to="shop/",
        verbose_name=_("Product Image"),
        help_text=_("The source product image to be displayed."),
    )

    # --- Image fields ---
    path_cropped = models.ImageField(
        upload_to="shop/",
        null=True,
        blank=True,
        verbose_name=_("Product Image Cropped"),
        help_text=_("Cropped product image managed by the admin image cropper."),
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
    external_url = models.URLField(
        blank=True,
        verbose_name=_("External URL"),
        help_text=_("Link to the product on an external shop or marketplace."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Only active products are shown in the public shop."),
    )

    objects = TranslatableManager()

    class Meta:
        verbose_name = _("Shop Product")
        verbose_name_plural = _("Shop Products")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        # BaseImage.__str__ uses "name" translation; our translatable field is "title"
        title = self.safe_translation_getter("title", any_language=True)
        return title if title else str(self.id)

    # ------------------------------------------------------------------
    # BaseImage overrides
    # ------------------------------------------------------------------

    def get_path_spec(self) -> ImageSpec:
        """Use THUMBNAIL spec (560px) for product images instead of landscape."""
        return settings.IMAGE_OPTIMIZATION_SPECS["THUMBNAIL"]

    def get_original_source(self) -> Any:
        """
        Prefer the cropped image as the source for WebP conversion and thumbnail
        generation. Falls back to BaseImage logic when no crop is present.
        """
        if self.path_cropped:
            return self.path_cropped
        return super().get_original_source()

    # ------------------------------------------------------------------
    # Save logic
    # ------------------------------------------------------------------

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        1. Reset path_cropped when the source image (path) changes without a new crop.
        2. Delegate to BaseImage.save() which handles process_image_task dispatch.
        3. Trigger automated translations.
        """
        if self.path_tracker.has_changed("path") and not self.path_tracker.has_changed(
            "path_cropped"
        ):
            self.path_cropped = None

        super().save(*args, **kwargs)
        self.trigger_translations()
