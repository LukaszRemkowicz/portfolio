import logging
from typing import Any

from parler.admin import TranslatableAdmin

from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from translation.mixins import (
    AutomatedTranslationAdminMixin,
    DynamicParlerStyleMixin,
    TranslationStatusMixin,
)
from users.types import CropperFieldConfig, CropperPreviewShape

from .forms import ShopProductAdminForm, ShopProductImageSelectWidget
from .models import ShopProduct, ShopSettings
from .types import FkCropperPayload

logger = logging.getLogger(__name__)


@admin.register(ShopProduct)
class ShopProductAdmin(DynamicParlerStyleMixin, TranslatableAdmin):
    """
    Admin interface for ShopProduct.
    Includes Parler translations and the custom image cropper.
    """

    form = ShopProductAdminForm
    list_display = (
        "get_title",
        "price",
        "currency",
        "is_active",
        "created_at",
    )
    list_editable = ("is_active",)
    list_display_links = ("get_title",)
    search_fields = ("translations__title", "translations__description")
    list_filter = ("is_active", "currency", "created_at")
    ordering = ("-created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                )
            },
        ),
        (
            _("Product Details"),
            {
                "fields": (
                    "price",
                    "currency",
                    "external_url",
                    "thumbnail_url",
                    "is_active",
                )
            },
        ),
        (
            _("Media"),
            {
                "fields": (
                    "image",
                    "thumbnail_cropped",
                ),
            },
        ),
    )

    change_form_template = "admin/shop/shopproduct/robust_change_form.html"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "image":
            kwargs["widget"] = ShopProductImageSelectWidget(
                db_field,
                self.admin_site,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=_("Title"), ordering="translations__title")
    def get_title(self, obj: ShopProduct) -> str:
        """Render the best available translated title in changelists and relation labels."""
        title = obj.safe_translation_getter("title", any_language=True)
        if not title:
            for lang in obj.get_available_languages():
                title = obj.safe_translation_getter("title", language_code=lang)
                if title:
                    break
        return str(title) if title else str(obj.id)

    @property
    def product_thumbnail_cropper_config(self) -> CropperFieldConfig:
        """Return the cropper configuration for the single shop product thumbnail field."""
        return CropperFieldConfig(
            field_name="image",
            label=_("Product Source Image"),
            input_id="id_image",
            target_field_name="thumbnail_cropped",
            target_input_id="id_thumbnail_cropped",
            preview_shape=CropperPreviewShape.ROUNDED_SQUARE,
            spec_method="get_thumbnail_spec",
            crop_aspect_ratio=4 / 3,
            output_dimension=560,
        )

    @property
    def cropper_visible_tab_panel(self) -> str:
        """Match the Jazzmin-generated tab id for the translated media fieldset."""
        return f"{slugify(str(_('Media')), allow_unicode=True)}-tab"

    @staticmethod
    def _get_source_image_url(request: HttpRequest, obj: ShopProduct) -> str:
        """Return the absolute AstroImage thumbnail URL used as the cropper source."""
        if not obj.image or not obj.image.thumbnail:
            return ""

        try:
            return request.build_absolute_uri(obj.image.thumbnail.url)
        except (ValueError, AttributeError):
            logger.warning(
                "Unable to build shop cropper source thumbnail URL",
                extra={"product_id": str(obj.pk)},
            )
            return ""

    def _build_fk_cropper_payload(
        self,
        request: HttpRequest,
        obj: ShopProduct | None,
    ) -> FkCropperPayload:
        """Build the JSON-ready payload consumed by the shop FK cropper widget."""
        lookup_url = reverse("shop-image-lookup")
        config = self.product_thumbnail_cropper_config
        output_dimension = config.output_dimension
        if output_dimension is None:
            logger.warning(
                "Shop cropper config missing output dimension; using default square",
                extra={"field_name": config.field_name},
            )
            output_dimension = 560
        output_width = output_dimension
        output_height = round(output_dimension / config.crop_aspect_ratio)
        source_image_url = self._get_source_image_url(request, obj) if obj else ""

        payload: FkCropperPayload = {
            "field_name": config.field_name,
            "label": str(config.label),
            "input_id": config.input_id,
            "target_field_name": config.target_field_name,
            "target_input_id": config.target_input_id,
            "preview_shape": config.preview_shape.value,
            "crop_aspect_ratio": config.crop_aspect_ratio,
            "visible_tab_panel": self.cropper_visible_tab_panel,
            "lookup_url": lookup_url,
            "source_image_url": source_image_url,
            "output_width": output_width,
            "output_height": output_height,
        }

        logger.debug(
            "Built shop FK cropper payload",
            extra={"product_id": str(obj.pk) if obj else None, "field_name": payload["field_name"]},
        )
        return payload

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        """
        Inject the FK cropper payload into both add and change product forms.
        """
        extra_context = extra_context or {}
        obj: ShopProduct | None = None
        if object_id:
            obj = self.get_object(request, object_id)

        extra_context["admin_fk_image_cropper"] = self._build_fk_cropper_payload(request, obj)
        return super().changeform_view(  # type: ignore[no-any-return]
            request, object_id, form_url, extra_context
        )


@admin.register(ShopSettings)
class ShopSettingsAdmin(
    AutomatedTranslationAdminMixin,
    TranslationStatusMixin,
    DynamicParlerStyleMixin,
    TranslatableAdmin,
):
    """
    Admin interface for ShopSettings singleton.
    """

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                )
            },
        ),
        (
            _("Background Image"),
            {
                "fields": (
                    "image",
                    "image_cropped",
                    "image_webp",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = ("translation_status", "image_webp", "updated_at")

    @property
    def change_form_template(self) -> str:
        """Force the robust template so the source-field cropper always mounts reliably."""
        return "admin/shop/shopsettings/robust_change_form.html"

    def get_change_form_base_template(self):
        """Avoid circular template extension when using a robust translatable form template."""
        return "admin/change_form.html"

    @property
    def cropper_field_configs(self) -> tuple[CropperFieldConfig, ...]:
        return (
            CropperFieldConfig(
                field_name="image",
                label=_("Background Source"),
                input_id="id_image",
                target_field_name="image_cropped",
                target_input_id="id_image_cropped",
                preview_shape=CropperPreviewShape.ROUNDED_SQUARE,
                spec_method="get_image_spec",
                crop_aspect_ratio=16 / 9,
            ),
        )

    @property
    def cropper_visible_tab_panel(self) -> str:
        """Match the Jazzmin-generated tab id for the translated background image fieldset."""
        return f"{slugify(str(_('Background Image')), allow_unicode=True)}-tab"

    def get_fieldsets(self, request: HttpRequest, obj: ShopSettings | None = None):
        """Show translation status on the default-language tab like other translated admins."""
        fieldsets = super().get_fieldsets(request, obj)
        if not obj:
            return fieldsets

        current_language = request.GET.get("language")
        default_language = settings.DEFAULT_APP_LANGUAGE
        if current_language and current_language != default_language:
            return fieldsets

        fieldsets = list(fieldsets)
        for index, (name, opts) in enumerate(fieldsets):
            fields = list(opts.get("fields", ()))
            if "title" in fields and "translation_status" not in fields:
                new_opts = opts.copy()
                fields.insert(0, "translation_status")
                new_opts["fields"] = tuple(fields)
                fieldsets[index] = (name, new_opts)
                break
        return tuple(fieldsets)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ) -> HttpResponse:
        """Inject translated language tabs and the shared source-field cropper payload."""
        extra_context = extra_context or {}
        obj: ShopSettings | None = None
        if object_id:
            obj = self.get_object(request, object_id)

        if obj:
            available_languages = self.get_available_languages(obj)
            extra_context["language_tabs"] = self.get_language_tabs(
                request, obj, available_languages
            )

        cropper_fields = []
        for field_config in self.cropper_field_configs:
            image_field = getattr(obj, field_config.field_name, None) if obj else None
            current_image_name = ""
            current_image_url = ""
            if image_field:
                current_image_name = str(image_field.name or "")
                try:
                    current_image_url = str(image_field.url)
                except ValueError:
                    current_image_url = ""

            spec = getattr(obj if obj else self.model, field_config.spec_method)()
            crop_aspect_ratio = field_config.crop_aspect_ratio or 1.0
            if crop_aspect_ratio >= 1:
                output_width = spec.dimension
                output_height = round(spec.dimension / crop_aspect_ratio)
            else:
                output_width = round(spec.dimension * crop_aspect_ratio)
                output_height = spec.dimension

            cropper_fields.append(
                {
                    "field_name": field_config.field_name,
                    "label": str(field_config.label),
                    "input_id": field_config.input_id,
                    "target_field_name": field_config.target_field_name,
                    "target_input_id": field_config.target_input_id,
                    "preview_shape": field_config.preview_shape.value,
                    "crop_aspect_ratio": crop_aspect_ratio,
                    "output_width": output_width,
                    "output_height": output_height,
                    "current_image_name": current_image_name,
                    "current_image_url": current_image_url,
                }
            )

        extra_context["admin_image_cropper"] = {
            "visible_tab_panel": self.cropper_visible_tab_panel,
            "component_title": _("Image Cropper"),
            "fields": cropper_fields,
            "default_field_name": "image",
        }

        return super().changeform_view(  # type: ignore[no-any-return]
            request, object_id, form_url, extra_context
        )

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Any | None = None,
    ):
        """Ensure the robust shop settings template wins over dynamic parler template selection."""
        response = super().render_change_form(request, context, add, change, form_url, obj)

        if isinstance(response, TemplateResponse):
            response.template_name = self.change_form_template

        return response

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Enforce singleton behavior by allowing only one ShopSettings instance."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)  # type: ignore[no-any-return]

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        """Prevent deletion of the singleton shop settings record from admin."""
        return False

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, Any] | None = None
    ) -> HttpResponse:
        """Redirect the changelist to the singleton change form when the record exists."""
        obj: ShopSettings | None = self.model.get_current()
        if not obj:
            return super().changelist_view(request, extra_context)  # type: ignore[no-any-return]
        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )
