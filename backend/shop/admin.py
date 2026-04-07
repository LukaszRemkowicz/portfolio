# backend/shop/admin.py
from typing import Any

from parler.admin import TranslatableAdmin

from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from .models import ShopProduct


@admin.register(ShopProduct)
class ShopProductAdmin(TranslatableAdmin):
    """
    Admin interface for ShopProduct.
    Includes Parler translations and the custom image cropper.
    """

    change_form_template = "admin/shop/shopproduct/robust_change_form.html"
    cropper_field_configs = settings.SHOP_PRODUCT_ADMIN_CROPPER_FIELD_CONFIGS

    list_display = (
        "title",
        "price",
        "currency",
        "is_active",
        "created_at",
    )
    list_editable = ("is_active",)
    list_display_links = ("title",)
    search_fields = ("translations__title", "translations__description")
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
                    "is_active",
                )
            },
        ),
        (
            _("Image Management"),
            {
                "fields": (
                    "path_cropped",
                    "path",
                ),
            },
        ),
    )

    readonly_fields = ()

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ):
        """
        Inject language_tabs and image cropper configurations into the template context.
        """
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)

        if obj:
            # Parler language tabs
            available_languages = self.get_available_languages(obj)
            extra_context["language_tabs"] = self.get_language_tabs(
                request, obj, available_languages
            )

            # Image Cropper setup
            cropper_fields = []
            for field_config in self.cropper_field_configs:
                field_name = field_config.field_name
                image_field = getattr(obj, field_name, None)
                current_image_name = ""
                current_image_url = ""

                if image_field:
                    current_image_name = str(image_field.name or "")
                    try:
                        current_image_url = str(image_field.url)
                    except ValueError:
                        current_image_url = ""

                spec = getattr(obj, field_config.spec_method)()
                crop_aspect_ratio = field_config.crop_aspect_ratio or 1.0

                if crop_aspect_ratio >= 1:
                    output_width = spec.dimension
                    output_height = round(spec.dimension / crop_aspect_ratio)
                else:
                    output_width = round(spec.dimension * crop_aspect_ratio)
                    output_height = spec.dimension

                cropper_fields.append(
                    {
                        "field_name": field_name,
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
                "visible_tab_panel": "general-tab",
                "component_title": _("Image Cropper"),
                "fields": cropper_fields,
            }

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Any | None = None,
    ):
        """
        Manually enforce our robust template to bypass base class shadowing.
        """
        response = super().render_change_form(request, context, add, change, form_url, obj)
        if isinstance(response, TemplateResponse):
            response.template_name = self.change_form_template
        return response
