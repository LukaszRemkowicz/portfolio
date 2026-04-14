import uuid
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from model_utils import FieldTracker
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.utils.image import ImageSpec, get_available_image_url
from core.models import SingletonModel
from shop.tasks import process_shop_settings_images_task
from translation.mixins import AutomatedTranslationModelMixin


class ShopProduct(AutomatedTranslationModelMixin, TranslatableModel):
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
    image_tracker = FieldTracker(fields=["image", "thumbnail_cropped"])

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
    thumbnail_cropped = models.ImageField(
        upload_to="shop/products/cropped/",
        null=True,
        blank=True,
        verbose_name=_("Thumbnail (Cropped)"),
        help_text=_(
            "Crop of the image specifically meant for the shop list card. Output of the FK cropper."
        ),
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

    objects = TranslatableManager()

    class Meta:
        verbose_name = _("Shop Product")
        verbose_name_plural = _("Shop Products")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return the translated product title when available, otherwise fall back to the UUID."""
        # BaseImage.__str__ uses "name" translation; our translatable field is "title"
        title = self.safe_translation_getter("title", any_language=True)
        return title if title else str(self.id)

    def get_thumbnail_spec(self) -> ImageSpec:
        """
        Return the specification for the shop product thumbnail.
        Matches the 4:3 shop-card crop used by the admin FK cropper.
        """
        return ImageSpec(dimension=560, quality=90, aspect_ratio=4 / 3)

    def get_thumbnail(self) -> str:
        """
        Return the primary display image for the shop product.
        Prioritizes the manually cropped thumbnail, then the linked
        AstroImage's standard generated thumbnail, then fails over to CDN.
        """
        cropped_url = get_available_image_url(self.thumbnail_cropped)
        if cropped_url:
            return cropped_url

        if self.image_id:
            thumbnail_url = get_available_image_url(self.image.thumbnail)
            if thumbnail_url:
                return thumbnail_url

        return self.thumbnail_url or ""

    # ------------------------------------------------------------------
    # Save logic
    # ------------------------------------------------------------------

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Clear stale manual crops and trigger translations when relevant."""
        image_changed: bool = self.image_tracker.has_changed("image")
        crop_changed: bool = self.image_tracker.has_changed("thumbnail_cropped")
        update_fields = kwargs.get("update_fields")

        if image_changed and not crop_changed:
            self.thumbnail_cropped = None

        super().save(*args, **kwargs)
        if not update_fields or any(
            field in update_fields for field in self.translation_trigger_fields
        ):
            self.trigger_translations()


class ShopSettings(AutomatedTranslationModelMixin, TranslatableModel, SingletonModel):
    """
    Singleton model to store global settings for the shop page.
    """

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

    image_webp = models.ImageField(
        upload_to="shop/backgrounds/",
        null=True,
        blank=True,
        verbose_name=_("Background WebP"),
        help_text=_("Auto-generated WebP version of the background."),
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

    @staticmethod
    def get_image_spec() -> ImageSpec:
        """Return the same 16:9 1920px shop background spec used previously."""
        return settings.IMAGE_OPTIMIZATION_SPECS.get(
            "LANDSCAPE_16_9", ImageSpec(dimension=1920, quality=90, aspect_ratio=16 / 9)
        )

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

        if source_changed and not cropped_changed:
            self.image_cropped = None

        super().save(*args, **kwargs)

        if (source_changed or cropped_changed) and not update_fields:
            process_shop_settings_images_task.delay_on_commit(self.pk)

        if not update_fields or any(
            field in update_fields for field in self.translation_trigger_fields
        ):
            self.trigger_translations()

    def get_serving_url(self) -> str:
        """Return the best available public background URL in derived-first order."""
        return (
            get_available_image_url(self.image_webp)
            or get_available_image_url(self.image_cropped)
            or get_available_image_url(self.image)
        )
