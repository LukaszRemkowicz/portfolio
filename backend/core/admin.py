from urllib.parse import urlencode
from uuid import UUID

from django import forms
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import RowNumber
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from astrophotography.models import AstroImage
from common.utils.signing import generate_signed_url_params

from .models import ImageVariant, LandingPageSettings
from .widgets import ThemedModelSelect2Widget, ThemedSelect2MultipleWidget


class ImageVariantAstroImageSearchWidget(ThemedModelSelect2Widget):
    """Search AstroImage records by translated name or slug."""

    search_fields = (
        "translations__name__icontains",
        "slug__icontains",
    )


class ImageVariantAstroImageFilterForm(forms.Form):
    """Searchable AstroImage selector for the ImageVariant changelist."""

    astroimage: forms.ModelChoiceField = forms.ModelChoiceField(
        queryset=AstroImage.objects.all(),
        required=False,
        label=_("AstroImage"),
    )

    def __init__(self, *args, admin_site, **kwargs):
        super().__init__(*args, **kwargs)
        del admin_site
        astroimage_field = self.fields["astroimage"]
        if not isinstance(astroimage_field, forms.ModelChoiceField):
            raise TypeError("ImageVariant AstroImage filter must be a ModelChoiceField.")

        astroimage_field.queryset = AstroImage.objects.prefetch_related("translations").order_by(
            "-created_at"
        )
        astroimage_field.widget = ImageVariantAstroImageSearchWidget(
            model=AstroImage,
            queryset=astroimage_field.queryset,
            attrs={
                "data-placeholder": _("Search AstroImage..."),
                "data-allow-clear": "true",
            },
        )


class ImageVariantChangeList(ChangeList):
    """ChangeList that treats astroimage as a custom admin control, not an ORM lookup."""

    astroimage_filter_parameter = "astroimage"

    def __init__(self, request, *args, **kwargs):
        original_get = request.GET
        selected_astroimage = original_get.get(self.astroimage_filter_parameter)
        if not selected_astroimage:
            super().__init__(request, *args, **kwargs)
            return

        request.imagevariant_astroimage_filter = selected_astroimage
        mutable_get = original_get.copy()
        mutable_get.pop(self.astroimage_filter_parameter, None)
        request.GET = mutable_get
        try:
            super().__init__(request, *args, **kwargs)
        finally:
            request.GET = original_get


@admin.register(ImageVariant)
class ImageVariantAdmin(admin.ModelAdmin):
    """Read-only inspection for generated responsive image variant rows."""

    change_list_template = "admin/core/imagevariant/change_list.html"
    list_display = (
        "order_number",
        "filename",
        "role",
        "dimensions",
        "mime_type",
    )
    list_display_links = ("order_number", "filename")
    list_filter = ("role", "mime_type", "content_type")
    ordering = ("-created_at", "-id")
    readonly_fields = (
        "id",
        "content_type",
        "object_id",
        "secure_file",
        "role",
        "width",
        "height",
        "mime_type",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = (
            super()
            .get_queryset(request)
            .annotate(
                admin_order_number=models.Window(
                    expression=RowNumber(),
                    order_by=(models.F("created_at").asc(), models.F("id").asc()),
                )
            )
        )
        image_id = getattr(request, "imagevariant_astroimage_filter", None)
        if not image_id and request:
            image_id = request.GET.get("astroimage")
        if not image_id:
            return queryset

        try:
            image_uuid = UUID(image_id)
        except ValueError:
            return queryset.none()

        content_type = ContentType.objects.get_for_model(AstroImage)
        return queryset.filter(content_type=content_type, object_id=image_uuid)

    def get_changelist(self, request, **kwargs):
        return ImageVariantChangeList

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["astroimage_filter_form"] = ImageVariantAstroImageFilterForm(
            data=request.GET or None,
            admin_site=self.admin_site,
        )
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description=_("No."))
    def order_number(self, obj):
        return obj.admin_order_number

    @admin.display(description=_("Filename"), ordering="file")
    def filename(self, obj):
        return obj.file.name.rsplit("/", 1)[-1] if obj.file else ""

    @admin.display(description=_("File"))
    def secure_file(self, obj):
        if not obj.file:
            return ""

        return format_html_join(
            "",
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            ((self._get_signed_file_url(obj), obj.file.name),),
        )

    @admin.display(description=_("Dimensions"), ordering="width")
    def dimensions(self, obj):
        return f"{obj.width} x {obj.height}"

    @staticmethod
    def _get_signed_file_url(obj):
        url = reverse(
            "admin-generic-secure-media",
            kwargs={
                "app_label": obj._meta.app_label,
                "model_name": obj._meta.model_name,
                "pk": str(obj.pk),
                "field_name": "file",
            },
        )
        sig_id = f"admin_media_{obj._meta.app_label}_{obj._meta.model_name}_{obj.pk}_file"
        params = generate_signed_url_params(sig_id, 3600)
        return f"{url}?{urlencode(params)}"


@admin.register(LandingPageSettings)
class LandingPageSettingsAdmin(admin.ModelAdmin):
    """Admin for the singleton LandingPageSettings model."""

    def has_add_permission(self, request):
        """Prevent creating more than one instance."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the settings."""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to the change page for the singleton instance."""
        obj = self.model.objects.last()
        if not obj:
            # If not seeded, let the standard view handle it or create one
            return super().changelist_view(request, extra_context)

        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context.update(
            {
                "show_save_and_continue": False,
                "show_save_and_add_another": False,
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    formfield_overrides = {
        models.ManyToManyField: {"widget": ThemedSelect2MultipleWidget(width="100%")},
    }

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "contact_form_enabled",
                    "travel_highlights_enabled",
                    "programming_enabled",
                    "lastimages_enabled",
                    "shop_enabled",
                    "latest_filters",
                    "meteors",
                )
            },
        ),
        (
            "Image Quality",
            {
                "fields": ("serve_webp_images",),
                "description": (
                    "Legacy WebP serving toggle. Responsive image variants are "
                    "generated by the 'backfill_image_variants' management command."
                ),
            },
        ),
    )
    list_display = (
        "__str__",
        "contact_form_enabled",
        "travel_highlights_enabled",
        "programming_enabled",
        "lastimages_enabled",
        "shop_enabled",
        "serve_webp_images",
        "meteors",
    )
