from typing import Any

from parler.admin import TranslatableAdmin

from django.conf import settings
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.types import ImageSpec
from translation.mixins import (
    AutomatedTranslationAdminMixin,
    DynamicParlerStyleMixin,
    TranslationStatusMixin,
)
from users.types import CropperFieldConfig, CropperPreviewShape

from .models import Project


@admin.register(Project)
class ProjectAdmin(
    AutomatedTranslationAdminMixin,
    TranslationStatusMixin,
    DynamicParlerStyleMixin,
    TranslatableAdmin,
):
    """Admin for programming projects: translated text plus a cropped cover screenshot."""

    list_display = ("thumbnail", "get_name", "technologies", "pricing", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "description", "technologies", "is_active")}),
        (_("Pricing"), {"fields": ("pricing", "price", "currency")}),
        (_("Links"), {"fields": ("github_url", "live_url")}),
        (_("Cover Image"), {"fields": ("image", "image_cropped")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("translation_status", "created_at", "updated_at")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Project]:
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("variants")  # type: ignore[no-any-return]

    @admin.display(description=_("Name"))
    def get_name(self, obj: Project) -> str:
        return str(obj)

    @admin.display(description=_("Thumbnail"))
    def thumbnail(self, obj: Project) -> str:
        """Render the thumbnail from DB variant rows only (no storage reads)."""
        variant = next(
            (v for v in obj.variants.all() if v.role == "thumbnail" and v.file),
            None,
        )
        if variant is None:
            return "-"
        return format_html(
            '<img src="{}" style="height:48px;border-radius:6px;" alt="">', variant.file.url
        )

    @property
    def change_form_template(self) -> str:
        """Force the robust template so the source-field cropper always mounts reliably."""
        return "admin/programming/project/robust_change_form.html"

    def get_change_form_base_template(self):
        """Avoid circular template extension when using a robust translatable form template."""
        return "admin/change_form.html"

    @property
    def cropper_field_configs(self) -> tuple[CropperFieldConfig, ...]:
        return (
            CropperFieldConfig(
                field_name="image",
                label=_("Cover Source"),
                input_id="id_image",
                target_field_name="image_cropped",
                target_input_id="id_image_cropped",
                preview_shape=CropperPreviewShape.ROUNDED_SQUARE,
                crop_aspect_ratio=16 / 10,
                spec=ImageSpec(dimension=1600, quality=90),
            ),
        )

    @property
    def cropper_visible_tab_panel(self) -> str:
        """Match the Jazzmin-generated tab id for the cover image fieldset."""
        return f"{slugify(str(_('Cover Image')), allow_unicode=True)}-tab"

    def get_fieldsets(self, request: HttpRequest, obj: Project | None = None):
        """Show translation status on the default-language tab like other translated admins."""
        fieldsets = super().get_fieldsets(request, obj)
        if not obj:
            return fieldsets

        current_language = request.GET.get("language")
        if current_language and current_language != settings.DEFAULT_APP_LANGUAGE:
            return fieldsets

        fieldsets = list(fieldsets)
        for index, (name, opts) in enumerate(fieldsets):
            fields = list(opts.get("fields", ()))
            if "name" in fields and "translation_status" not in fields:
                new_opts = opts.copy()
                new_opts["fields"] = ("translation_status", *fields)
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
        obj: Project | None = self.get_object(request, object_id) if object_id else None

        if obj:
            extra_context["language_tabs"] = self.get_language_tabs(
                request, obj, self.get_available_languages(obj)
            )

        cropper_fields = []
        for config in self.cropper_field_configs:
            image_field = getattr(obj, config.field_name, None) if obj else None
            current_image_name = ""
            current_image_url = ""
            if image_field:
                current_image_name = str(image_field.name or "")
                try:
                    current_image_url = str(image_field.url)
                except ValueError:
                    current_image_url = ""

            crop_aspect_ratio = config.crop_aspect_ratio or 1.0
            dimension = config.spec.dimension
            if crop_aspect_ratio >= 1:
                output_width, output_height = dimension, round(dimension / crop_aspect_ratio)
            else:
                output_width, output_height = round(dimension * crop_aspect_ratio), dimension

            cropper_fields.append(
                {
                    "field_name": config.field_name,
                    "label": str(config.label),
                    "input_id": config.input_id,
                    "target_field_name": config.target_field_name,
                    "target_input_id": config.target_input_id,
                    "preview_shape": config.preview_shape.value,
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
        """Ensure the robust template wins over dynamic parler template selection."""
        response = super().render_change_form(request, context, add, change, form_url, obj)
        if isinstance(response, TemplateResponse):
            response.template_name = self.change_form_template
        return response
