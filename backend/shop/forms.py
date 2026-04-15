from parler.forms import TranslatableModelForm

from django import forms
from django.contrib.admin.widgets import AutocompleteSelect
from django.utils.translation import gettext_lazy as _

from .models import ShopProduct


class ShopProductImageSelectWidget(AutocompleteSelect):
    """Admin autocomplete widget styled to match the project's themed Select2 fields."""

    def __init__(self, field, admin_site, attrs=None, choices=(), using=None):
        merged_attrs = {
            "data-placeholder": _("Select image..."),
            "data-allow-clear": "true",
            "data-autocomplete-light-function": "select2",
            "style": "width: 100%; max-width: 100ch;",
            "class": "themed-select2 shop-product-image-select",
        }
        if attrs:
            merged_attrs.update(attrs)
        super().__init__(field, admin_site, attrs=merged_attrs, choices=choices, using=using)

    @property
    def media(self):
        # Admin autocomplete widgets already ship their own Select2 JS wiring.
        # Only add our theme CSS here; pulling in django-select2 media as well can
        # initialize the same field twice and duplicate dropdown results.
        return super().media + forms.Media(css={"all": ("core/css/select2_admin.css",)})


class ShopProductAdminForm(TranslatableModelForm):
    class Meta:
        model = ShopProduct
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        image_field = self.fields.get("image")
        if not image_field:
            return

        image_field.queryset = image_field.queryset.order_by("pk").distinct()
        image_field.help_text = _("Select an existing gallery image for this product.")
