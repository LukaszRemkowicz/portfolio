from typing import Any
from urllib.parse import urlencode

from django_countries import countries
from parler.forms import TranslatableModelForm

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminDateWidget, FilteredSelectMultiple
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from common.utils.signing import generate_signed_url_params
from core.forms import RangeField
from core.widgets import (
    CountrySelect2Widget,
    SecureAdminFileWidget,
    ThemedSelect2MultipleWidget,
    ThemedSelect2Widget,
)

from .models import AstroImage, MainPageBackgroundImage, MeteorsMainPageConfig, Place, Tag
from .protocols import SupportsBaseImageUploadForm


class BaseImageSourceUploadFormMixin:
    """Expose the source upload field in admin while hiding the legacy model field."""

    def _configure_source_upload_field(self: SupportsBaseImageUploadForm) -> None:
        """Hide the legacy model field and configure the source upload field."""
        # TODO: legacy field, will be removed in future.
        self.fields.pop("path", None)

        current_source = self._get_current_source_field()
        self.fields["original_upload"].required = not bool(current_source)

        if self.instance.pk and current_source:
            self._init_secure_original_widget(current_source)

    def _get_current_source_field(self: SupportsBaseImageUploadForm) -> Any:
        return self.instance.original_field

    def _init_secure_original_widget(
        self: SupportsBaseImageUploadForm, current_source: Any
    ) -> None:
        """Configure the source upload widget with a signed secure URL."""
        app_label = self.instance._meta.app_label
        model_name = self.instance._meta.model_name
        pk = self.instance.pk
        url = reverse(
            "admin-generic-secure-media",
            kwargs={
                "app_label": app_label,
                "model_name": model_name,
                "pk": str(pk),
                "field_name": "original",
            },
        )
        sig_id = f"admin_media_{app_label}_{model_name}_{pk}_original"
        params = generate_signed_url_params(sig_id, 3600)
        full_url = f"{url}?{urlencode(params)}"
        filename = current_source.name.split("/")[-1]

        self.fields["original_upload"].widget = SecureAdminFileWidget(
            signed_url=full_url, label=filename
        )

    def _apply_uploaded_original(self: SupportsBaseImageUploadForm) -> None:
        """Copy the admin upload field into the canonical source field."""
        uploaded_original = self.cleaned_data.get("original_upload")
        if uploaded_original:
            self.instance.original = uploaded_original

    def _validate_current_source_exists(
        self: SupportsBaseImageUploadForm, cleaned_data: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Reject editing a broken row when the current stored source file is missing."""
        uploaded_original = cleaned_data.get("original_upload") if cleaned_data else None
        current_source = self._get_current_source_field()
        current_source_name = str(getattr(current_source, "name", "") or "")

        if self.instance.pk and not uploaded_original and current_source_name:
            try:
                if not current_source.storage.exists(current_source_name):
                    self.add_error(
                        "original_upload",
                        _(
                            "The selected image file does not exist in storage. "
                            "Please upload it again."
                        ),
                    )
            except (OSError, ValueError):
                self.add_error(
                    "original_upload",
                    _(
                        "The selected image file could not be validated in storage. "
                        "Please upload it again."
                    ),
                )

        return cleaned_data

    def _remap_source_upload_errors(self: SupportsBaseImageUploadForm, errors: Any) -> None:
        """Map model validation errors onto the admin source upload field."""
        error_dict = getattr(errors, "error_dict", None)
        if error_dict:
            for field_name in ["original", "path"]:
                if field_name in error_dict:
                    error_dict.setdefault("original_upload", []).extend(error_dict.pop(field_name))


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


class AstroImageForm(BaseImageSourceUploadFormMixin, TranslatableModelForm):
    original_upload = forms.ImageField(required=True, label=_("Original Image"))
    tags = forms.ModelMultipleChoiceField(  # type: ignore[var-annotated]
        queryset=Tag.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Tags", is_stacked=False),
        label="Tags",
    )

    class Meta:
        model = AstroImage
        exclude = ("calculated_exposure_hours",)
        widgets = {
            "capture_date": AdminDateWidget(),
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
        return self._validate_current_source_exists(cleaned_data)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_place_queryset()
        self._init_location_choices()
        self._init_tags_initial_data()
        self._init_name_field_validation()
        self._configure_source_upload_field()

    def _init_place_queryset(self) -> None:
        """Fix duplicate places in dropdown by clearing ordering."""
        if "place" in self.fields:
            self.fields["place"].queryset = Place.objects.order_by("pk").distinct()

    def _init_location_choices(self) -> None:
        """Enhance location (country) labels with codes for better searchability."""
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

    def _init_tags_initial_data(self) -> None:
        """Set initial tags for existing instances."""
        if self.instance.pk:
            self.fields["tags"].initial = self.instance.tags.all()

    def _init_name_field_validation(self) -> None:
        """Enforce 'name' as required for the default language (English)."""
        current_lang = self.instance.get_current_language()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        if current_lang == default_lang and "name" in self.fields:
            self.fields["name"].required = True

    def _post_clean(self) -> None:
        self._apply_uploaded_original()
        super()._post_clean()

    def _update_errors(self, errors) -> None:
        self._remap_source_upload_errors(errors)
        super()._update_errors(errors)


class MainPageBackgroundImageForm(BaseImageSourceUploadFormMixin, TranslatableModelForm):
    """Custom form for main page background images."""

    original_upload = forms.ImageField(required=False, label=_("Original Image"))

    class Meta:
        model = MainPageBackgroundImage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configure_source_upload_field()

    def clean(self):
        cleaned_data = super().clean()
        return self._validate_current_source_exists(cleaned_data)

    def _post_clean(self) -> None:
        self._apply_uploaded_original()
        super()._post_clean()

    def _update_errors(self, errors) -> None:
        self._remap_source_upload_errors(errors)
        super()._update_errors(errors)


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
