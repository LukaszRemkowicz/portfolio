from django_countries import countries
from parler.forms import TranslatableModelForm

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _

from core.forms import RangeField
from core.widgets import (
    CountrySelect2Widget,
    ThemedSelect2MultipleWidget,
    ThemedSelect2Widget,
)

from .models import AstroImage, MeteorsMainPageConfig, Place, Tag


class PlaceAdminForm(TranslatableModelForm):
    """Custom form for Place admin to use Select2 widget for country field."""

    # Explicitly define country field to override django-countries default widget
    country = forms.ChoiceField(
        choices=[("", "---------")] + list(countries),
        widget=CountrySelect2Widget(),
        required=False,
        label=_("Country"),
        help_text=_("Required for regular places. Leave blank for multi-country regions."),
    )
    sub_places = forms.ModelMultipleChoiceField(
        queryset=Place.objects.all(),
        widget=ThemedSelect2MultipleWidget(
            attrs={
                "data-placeholder": _("Select sub-places for this region..."),
            }
        ),
        required=False,
        label=_("Sub-Places"),
        help_text=_(
            "For regions: the specific sub-places covered by this region "
            "(e.g. Hawaii → Oahu, Big Island)."
        ),
    )

    class Meta:
        model = Place
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude this place from its own sub_places to prevent circular references
        if self.instance.pk:
            self.fields["sub_places"].queryset = Place.objects.exclude(pk=self.instance.pk)
        else:
            self.fields["sub_places"].queryset = Place.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        is_region = cleaned_data.get("is_region", False)
        country = cleaned_data.get("country")
        if not is_region and not country:
            self.add_error("country", _("Country is required for non-region places."))
        return cleaned_data


class TagAdminForm(TranslatableModelForm):
    """Custom form for Tag admin to handle readonly slug validation gracefully."""

    class Meta:
        model = Tag
        exclude = ("slug",)


class AstroImageForm(TranslatableModelForm):
    tags = forms.ModelMultipleChoiceField(  # type: ignore[var-annotated]
        queryset=Tag.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Tags", is_stacked=False),
        label="Tags",
    )

    class Meta:
        model = AstroImage
        fields = "__all__"
        widgets = {
            "location": ThemedSelect2Widget(),
            "place": ThemedSelect2Widget(
                tags=True,
                attrs={
                    "data-placeholder": _("Select or type place..."),
                    "data-allow-clear": "true",
                },
            ),
            "telescope": ThemedSelect2MultipleWidget(
                attrs={
                    "data-placeholder": _("Select telescope(s)..."),
                },
            ),
            "camera": ThemedSelect2MultipleWidget(
                attrs={
                    "data-placeholder": _("Select camera(s)..."),
                },
            ),
            "lens": ThemedSelect2MultipleWidget(
                attrs={
                    "data-placeholder": _("Select lens(es)..."),
                },
            ),
            "tracker": ThemedSelect2MultipleWidget(
                attrs={
                    "data-placeholder": _("Select mount/tracker(s)..."),
                },
            ),
            "tripod": ThemedSelect2MultipleWidget(
                attrs={
                    "data-placeholder": _("Select tripod(s)..."),
                },
            ),
        }

    def clean_place(self):
        place = self.cleaned_data.get("place")
        if not place:
            # If empty, but we might have typed something
            place_name = self.data.get("place")
            if place_name:
                place, _ = Place.objects.get_or_create(name=place_name)
        elif isinstance(place, str):
            # If Select2 returned the string directly because it's a new tag
            place, _ = Place.objects.get_or_create(name=place)
        return place

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            return None
        telescope = cleaned_data.get("telescope")
        lens = cleaned_data.get("lens")

        if telescope and telescope.exists() and lens and lens.exists():
            raise forms.ValidationError(
                _("Cannot have both telescope and lens. Please choose one or the other.")
            )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fix duplicate places in dropdown by clearing ordering (which uses properties/joins)
        if "place" in self.fields:
            self.fields["place"].queryset = Place.objects.order_by("pk").distinct()

        # Enhance location (country) labels with codes for better searchability
        location_field = self.fields.get("location")
        if isinstance(location_field, forms.ChoiceField):
            enhanced_choices = [("", "---------")]
            for code, name in location_field.choices:  # type: ignore[misc, union-attr]
                if code:
                    alpha3 = countries.alpha3(code)
                    label = f"{name} ({code}"
                    if alpha3:
                        label += f", {alpha3}"
                    label += ")"
                    enhanced_choices.append((code, label))
            location_field.choices = enhanced_choices

        if self.instance.pk:
            self.fields["tags"].initial = self.instance.tags.all()

        # Enforce 'name' as required for the default language (English)
        # since we added blank=True to the model to allow clearing translations.
        current_lang = self.instance.get_current_language()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        if current_lang == default_lang and "name" in self.fields:
            self.fields["name"].required = True


class MeteorsMainPageConfigForm(forms.ModelForm):
    """
    Custom form using MultiWidget to render min/max inputs in a single row
    with the description at the bottom.
    """

    star_path_range = RangeField(
        field_class=forms.IntegerField,
        placeholder_min=_("min in pixels"),
        placeholder_max=_("max in pixels"),
        label=_("Star Path"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "regular star in pixels. Example: [50, 500]"
        ),
        required=False,
    )

    bolid_path_range = RangeField(
        field_class=forms.IntegerField,
        placeholder_min=_("min in pixels"),
        placeholder_max=_("max in pixels"),
        label=_("Bolid Path"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "bolid in pixels. Example: [50, 500]"
        ),
        required=False,
    )

    star_streak_range = RangeField(
        field_class=forms.IntegerField,
        placeholder_min=_("min in pixels"),
        placeholder_max=_("max in pixels"),
        label=_("Star Streak"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of "
            "a regular star. Example: [100, 200]"
        ),
        required=False,
    )

    bolid_streak_range = RangeField(
        field_class=forms.IntegerField,
        placeholder_min=_("min in pixels"),
        placeholder_max=_("max in pixels"),
        label=_("Bolid Streak"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of a bolid. "
            "Example: [20, 100]"
        ),
        required=False,
    )

    star_duration_range = RangeField(
        field_class=forms.FloatField,
        placeholder_min=_("min (s)"),
        placeholder_max=_("max (s)"),
        label=_("Star Duration"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a regular star. "
            "Example: [0.4, 1.2]"
        ),
        required=False,
    )

    bolid_duration_range = RangeField(
        field_class=forms.FloatField,
        placeholder_min=_("min (s)"),
        placeholder_max=_("max (s)"),
        label=_("Bolid Duration"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a bolid. "
            "Example: [0.4, 0.9]"
        ),
        required=False,
    )

    star_opacity_range = RangeField(
        field_class=forms.FloatField,
        placeholder_min=_("min (0.0-1.0)"),
        placeholder_max=_("max (0.0-1.0)"),
        label=_("Star Opacity"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for regular star brightness. "
            "Example: [0.4, 0.8]"
        ),
        required=False,
    )

    bolid_opacity_range = RangeField(
        field_class=forms.FloatField,
        placeholder_min=_("min (0.0-1.0)"),
        placeholder_max=_("max (0.0-1.0)"),
        label=_("Bolid Opacity"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for bolid brightness. "
            "Example: [0.7, 1.0]"
        ),
        required=False,
    )

    smoke_opacity_range = RangeField(
        field_class=forms.FloatField,
        placeholder_min=_("min (0.0-1.0)"),
        placeholder_max=_("max (0.0-1.0)"),
        label=_("Smoke Opacity"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for the smoke trail of a bolid. "
            "Example: [0.5, 0.8]"
        ),
        required=False,
    )

    class Meta:
        model = MeteorsMainPageConfig
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return None

        json_fields = [
            "star_path_range",
            "bolid_path_range",
            "star_streak_range",
            "bolid_streak_range",
            "star_opacity_range",
            "bolid_opacity_range",
            "smoke_opacity_range",
            "star_duration_range",
            "bolid_duration_range",
        ]

        for field in json_fields:
            val = cleaned_data.get(field)
            # If value is empty list or None, apply model default
            if not val:
                model_field = self._meta.model._meta.get_field(field)
                default = model_field.default
                if callable(default):
                    cleaned_data[field] = default()
                else:
                    cleaned_data[field] = default

        return cleaned_data
