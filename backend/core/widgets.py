from django_select2.forms import Select2MultipleWidget, Select2Widget

from django import forms
from django.utils.translation import gettext_lazy as _


class ThemedSelect2Widget(Select2Widget):
    """
    A Select2Widget that automatically includes project-wide dark mode styling.
    """

    def __init__(self, *args, **kwargs):
        width = kwargs.pop("width", "auto")
        tags = kwargs.pop("tags", False)
        attrs = kwargs.get("attrs", {})

        # Placeholder logic
        placeholder = attrs.get("data-placeholder", _("Select..."))
        attrs.setdefault("data-placeholder", placeholder)
        attrs.setdefault("data-allow-clear", "false")

        if tags:
            attrs.setdefault("data-tags", "true")

        attrs["style"] = f"width: {width}; max-width: 100ch;"
        attrs["class"] = attrs.get("class", "") + " themed-select2"
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)

    @property
    def media(self):
        return super().media + forms.Media(css={"all": ("core/css/select2_admin.css",)})


class ThemedSelect2MultipleWidget(Select2MultipleWidget):
    """
    A Select2MultipleWidget that automatically includes project-wide dark mode styling.
    """

    def __init__(self, *args, **kwargs):
        width = kwargs.pop("width", "auto")
        attrs = kwargs.get("attrs", {})
        attrs.setdefault("data-placeholder", _("Select images..."))
        attrs.setdefault("data-allow-clear", "false")
        attrs["style"] = f"width: {width}; max-width: 100ch;"
        attrs["class"] = attrs.get("class", "") + " themed-select2"
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)

    @property
    def media(self):
        return super().media + forms.Media(css={"all": ("core/css/select2_admin.css",)})


class ReadOnlyMessageWidget(forms.Widget):
    """
    A simple widget to display a read-only message in the same style as Select2 boxes.
    """

    template_name = "core/widgets/read_only_message.html"

    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["message"] = self.message
        return context

    @property
    def media(self):
        return forms.Media(css={"all": ("core/css/select2_admin.css",)})


class CountrySelect2Widget(ThemedSelect2Widget):
    """
    A Select2Widget specifically for country fields that allows searching by both
    country name and country code (e.g., 'US', 'PL', 'GB').

    This widget can be reused across any model that needs a country selection field.

    Usage:
        from core.widgets import CountrySelect2Widget

        class MyForm(forms.Form):
            country = forms.ChoiceField(
                choices=list(countries),
                widget=CountrySelect2Widget()
            )
    """

    def __init__(self, *args, **kwargs):
        # Set default placeholder for country selection
        attrs = kwargs.get("attrs", {})
        attrs.setdefault("data-placeholder", _("Select country..."))
        attrs.setdefault("data-allow-clear", "true")
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)

    def optgroups(self, name, value, attrs=None):
        """
        Override optgroups to add country codes to the option text for better searchability.
        This allows users to search by typing either the country name or the 2-letter code.
        """
        groups = super().optgroups(name, value, attrs)

        # Enhance each option with the country code in the display text
        for group in groups:
            for option in group[1]:
                # option structure: (option_value, option_label, selected, index, attrs)
                if option.get("value"):  # Skip empty option
                    code = option["value"]
                    label = option["label"]
                    # Format: "United States (US)" for better searchability
                    option["label"] = f"{label} ({code})"

        return groups
