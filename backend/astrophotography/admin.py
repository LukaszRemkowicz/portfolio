from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.widgets import ReadOnlyMessageWidget, ThemedSelect2MultipleWidget, ThemedSelect2Widget

from .forms import AstroImageForm
from .models import AstroImage, MainPageBackgroundImage, MainPageLocationSlider, Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(AstroImage)
class AstroImageAdmin(admin.ModelAdmin):
    form = AstroImageForm
    list_display = ("name", "capture_date", "location", "place", "has_thumbnail", "tag_list")
    list_filter = ("celestial_object", "tags")
    search_fields = ("name", "description", "location", "place__name", "equipment")

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())

    ordering = ("-capture_date", "-created_at")

    @admin.display(boolean=True, description="Has Thumbnail")
    def has_thumbnail(self, obj):
        return bool(obj.thumbnail)

    fieldsets = (
        (None, {"fields": ("name", "description", "path", "tags")}),
        (
            "Capture Details",
            {
                "fields": (
                    "capture_date",
                    "location",
                    "place",
                    "celestial_object",
                    "equipment",
                    "exposure_details",
                )
            },
        ),
        ("Processing", {"fields": ("processing_details",)}),
        ("Links", {"fields": ("astrobin_url",)}),
        ("Thumbnail", {"fields": ("thumbnail",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

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


class MainPageLocationSliderForm(forms.ModelForm):
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
            self.fields["images"].widget = ReadOnlyMessageWidget(
                message=_("Save the slider first to select images for this country.")
            )

    class Meta:
        model = MainPageLocationSlider
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
        }

    def clean_place(self):
        place = self.cleaned_data.get("place")
        if not place:
            place_name = self.data.get("place")
            if place_name:
                place, _ = Place.objects.get_or_create(name=place_name)
        elif isinstance(place, str):
            place, _ = Place.objects.get_or_create(name=place)
        return place


@admin.register(MainPageLocationSlider)
class MainPageLocationSliderAdmin(admin.ModelAdmin):
    form = MainPageLocationSliderForm
    list_display = ("pk", "country", "place", "highlight_name", "is_active")
    list_display_links = ("pk", "country")
    list_filter = ("is_active", "country", "place")
    search_fields = ("country", "place__name", "highlight_name")
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "highlight_name",
        "country",
        "place",
        "is_active",
        "images",
        "created_at",
        "updated_at",
    )

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(request, obj, **kwargs)
