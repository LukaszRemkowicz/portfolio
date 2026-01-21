from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.widgets import ReadOnlyMessageWidget, ThemedSelect2MultipleWidget, ThemedSelect2Widget

from .forms import AstroImageForm
from .models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MainPageLocation,
    Place,
    Telescope,
    Tracker,
    Tripod,
)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("model",)
    search_fields = ("model",)


@admin.register(Lens)
class LensAdmin(admin.ModelAdmin):
    list_display = ("model",)
    search_fields = ("model",)


@admin.register(Telescope)
class TelescopeAdmin(admin.ModelAdmin):
    list_display = ("model",)
    search_fields = ("model",)


@admin.register(Tracker)
class TrackerAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Tripod)
class TripodAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AstroImage)
class AstroImageAdmin(admin.ModelAdmin):
    form = AstroImageForm
    list_display = ("name", "capture_date", "location", "place", "has_thumbnail", "tag_list")
    list_filter = ("celestial_object", "tags")
    search_fields = (
        "name",
        "description",
        "location",
        "place__name",
        "camera__model",
        "lens__model",
        "telescope__model",
        "tracker__name",
        "tripod__name",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "capture_date",
                    "astrobin_url",
                )
            },
        ),
        (
            _("Media"),
            {
                "fields": ("path", "thumbnail"),
            },
        ),
        (
            _("Tags"),
            {
                "fields": ("celestial_object", "tags"),
            },
        ),
        (
            _("Where image was taken?"),
            {
                "fields": ("location", "place"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Equipment"),
            {
                "fields": ("telescope", "camera", "lens", "tracker", "tripod"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Technical Details"),
            {
                "fields": ("exposure_details", "processing_details"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())

    ordering = ("-capture_date", "-created_at")

    @admin.display(boolean=True, description="Has Thumbnail")
    def has_thumbnail(self, obj):
        return bool(obj.thumbnail)

    readonly_fields = ("created_at", "updated_at", "thumbnail")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        # Hide "Save and add another" button when editing (only show when adding)
        if object_id:
            extra_context["show_save_and_add_another"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(MainPageBackgroundImage)
class MainPageBackgroundImageAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "description", "path")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class MainPageLocationForm(forms.ModelForm):
    images = forms.ModelMultipleChoiceField(
        queryset=AstroImage.objects.all(),
        widget=ThemedSelect2MultipleWidget(),
        required=False,
        label=_("Images"),
        help_text=_(
            "Select images to display in the slideshow for this location "
            "(filtered by country and place)."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django_countries import countries

        # Enhance country labels
        enhanced_choices = [("", "---------")]
        for code, name in self.fields["country"].choices:
            if code:
                alpha3 = countries.alpha3(code)
                label = f"{name} ({code}"
                if alpha3:
                    label += f", {alpha3}"
                label += ")"
                enhanced_choices.append((code, label))
        self.fields["country"].choices = enhanced_choices

        # Dynamic filtering for images field
        if self.instance.pk:
            # Edit mode
            qs = AstroImage.objects.filter(
                location=self.instance.country, place=self.instance.place
            )
            self.fields["images"].queryset = qs
            self.fields["background_image"].queryset = qs

            if not qs.exists():
                self.fields["images"].widget = ReadOnlyMessageWidget(
                    message=_("No matching items found for this country and place.")
                )
                self.fields["images"].help_text = _(
                    "Please add images with these location details in the "
                    "'Astrophotography Images' section first."
                )
        else:
            # Creation mode
            self.fields["images"].queryset = AstroImage.objects.none()
            self.fields["background_image"].queryset = AstroImage.objects.none()
            self.fields["images"].widget = ReadOnlyMessageWidget(
                message=_("Save the slider first to select images for this country.")
            )

    class Meta:
        model = MainPageLocation
        fields = "__all__"
        widgets = {
            "country": ThemedSelect2Widget(),
            "place": ThemedSelect2Widget(
                tags=True,
                attrs={
                    "data-placeholder": _("Select or type place..."),
                    "data-allow-clear": "true",
                },
            ),
            "background_image": ThemedSelect2Widget(
                attrs={
                    "data-placeholder": _("Select background image..."),
                    "data-allow-clear": "true",
                },
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get("country")
        images = cleaned_data.get("images")

        if country and images:
            for image in images:
                if image.location != country:
                    raise forms.ValidationError(
                        _(
                            "Image '%(image)s' (%(location)s) does not match "
                            "the slider's country (%(country)s)."
                        )
                        % {
                            "image": image.name,
                            "location": image.location.name if image.location else "Unknown",
                            "country": country.name,
                        }
                    )
        return cleaned_data

    def clean_place(self):
        place = self.cleaned_data.get("place")
        if not place:
            place_name = self.data.get("place")
            if place_name:
                place, _ = Place.objects.get_or_create(name=place_name)
        elif isinstance(place, str):
            place, _ = Place.objects.get_or_create(name=place)
        return place


@admin.register(MainPageLocation)
class MainPageLocationAdmin(admin.ModelAdmin):
    form = MainPageLocationForm
    list_display = ("pk", "country", "place", "highlight_name", "is_active")
    list_display_links = ("pk", "country")
    list_filter = ("is_active", "country", "place")
    search_fields = ("country", "place__name", "highlight_name")
    readonly_fields = ("created_at", "updated_at", "country_slug", "place_slug")
    fields = (
        "highlight_name",
        "country",
        "place",
        "country_slug",
        "place_slug",
        "is_active",
        "story",
        "background_image",
        "images",
        "created_at",
        "updated_at",
    )

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(request, obj, **kwargs)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        # Hide "Save and add another" button when editing (only show when adding)
        if object_id:
            extra_context["show_save_and_add_another"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)
