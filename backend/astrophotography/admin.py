from django_countries import countries

from django import forms
from django.contrib import admin, messages
from django.contrib.postgres.forms import RangeWidget
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.widgets import ReadOnlyMessageWidget, ThemedSelect2MultipleWidget, ThemedSelect2Widget

from .forms import AstroImageForm, MeteorsMainPageConfigForm
from .models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MainPageLocation,
    MeteorsMainPageConfig,
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
    list_display = ("model",)
    search_fields = ("model",)


@admin.register(Tripod)
class TripodAdmin(admin.ModelAdmin):
    list_display = ("model",)
    search_fields = ("model",)


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
        "tracker__model",
        "tripod__model",
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
        """
        Customizes the change form view to hide certain buttons.

        Specifically, hides the 'Save and add another' button when editing
        an existing object to streamline the UI.
        """
        extra_context = extra_context or {}
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
        self._enhance_country_labels()
        self._apply_dynamic_filtering()

    def _enhance_country_labels(self):
        """
        Enhance the country choice labels in the form with ISO Alpha-3 codes.

        Transforms default country names (e.g., 'Poland') into a more detailed
        format including Alpha-2 and Alpha-3 codes (e.g., 'Poland (PL, POL)')
        to improve administrative scanning and data verification.
        """
        country_field = self.fields.get("country")
        if isinstance(country_field, forms.ChoiceField):
            enhanced_choices = [("", "---------")]
            for code, name in country_field.choices:  # type: ignore[misc, union-attr]
                if code:
                    alpha3 = countries.alpha3(code)
                    label = f"{name} ({code}"
                    if alpha3:
                        label += f", {alpha3}"
                    label += ")"
                    enhanced_choices.append((code, label))
            country_field.choices = enhanced_choices

    def _apply_dynamic_filtering(self):  # noqa: C901
        """
        Dynamically filter the available images based on the selected country and place.

        Ensures that 'images' and 'background_image' querysets only contain images
        matching the specific location of this Travel Highlight.

        Logic:
        - Edit mode: Filters by instance country/place.
        - Creation mode: Disables selection (queryset.none()) until the record is saved,
          as the filtering context depends on persisted location data.
        """
        # Dynamic filtering for images field
        if self.instance.pk:
            # Edit mode
            qs = AstroImage.objects.filter(
                location=self.instance.country, place=self.instance.place
            )
            images_field = self.fields.get("images")
            if isinstance(images_field, forms.ModelChoiceField):
                images_field.queryset = qs

            bg_image_field = self.fields.get("background_image")
            if isinstance(bg_image_field, forms.ModelChoiceField):
                bg_image_field.queryset = qs

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
            images_field = self.fields.get("images")
            if isinstance(images_field, forms.ModelChoiceField):
                images_field.queryset = AstroImage.objects.none()

            bg_image_field = self.fields.get("background_image")
            if isinstance(bg_image_field, forms.ModelChoiceField):
                bg_image_field.queryset = AstroImage.objects.none()
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
            "adventure_date": RangeWidget(
                base_widget=forms.DateInput(attrs={"type": "date", "onclick": "this.showPicker()"})
            ),
        }

    def clean(self):
        """
        Perform cross-field validation for the Travel Highlight slider.

        Specifically, ensures that all selected images are captured in the same
        country as the slider itself. This prevents geographic data inconsistency
        in the gallery view.
        """
        cleaned_data = super().clean()
        if cleaned_data is None:
            return None
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

    class Media:
        css = {
            "all": (
                "core/css/select2_admin.css",
                "core/css/admin_date_clean.css",
            )
        }

    fields = (
        "highlight_name",
        "country",
        "place",
        "adventure_date",
        "country_slug",
        "place_slug",
        "is_active",
        "story",
        "background_image",
        "images",
        "created_at",
        "updated_at",
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        # Hide "Save and add another" button when editing (only show when adding)
        if object_id:
            extra_context["show_save_and_add_another"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(MeteorsMainPageConfig)
class MeteorsMainPageConfigAdmin(admin.ModelAdmin):
    """
    Admin configuration for the shooting stars (meteors) effect.
    Ensures that only one configuration instance can exist.
    """

    form = MeteorsMainPageConfigForm
    list_display = ("__str__", "updated_at")
    readonly_fields = ("updated_at",)

    fieldsets = (
        (
            _("General Settings"),
            {
                "fields": ("random_stars_shooting", "bolid_chance", "bolid_interval"),
                "description": _(
                    "Control the basic behavior of shooting stars and "
                    "their special 'bolid' variants."
                ),
            },
        ),
        (
            _("Standard Star Appearance"),
            {
                "fields": (
                    "star_path_range",
                    "star_streak_range",
                    "star_duration_range",
                    "star_opacity_range",
                ),
                "description": _(
                    "Define the visual properties of regular (non-bolid) shooting stars. "
                ),
            },
        ),
        (
            _("Bolid (Fireball) Appearance"),
            {
                "fields": (
                    "bolid_path_range",
                    "bolid_streak_range",
                    "bolid_duration_range",
                    "bolid_opacity_range",
                    "smoke_opacity_range",
                ),
                "description": _(
                    "Configure the more dramatic bolid effects, including their smoke trails."
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("updated_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        # Only allow adding if no instance exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the last configuration
        if self.model.objects.count() <= 1:
            return False
        return super().has_delete_permission(request, obj)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        opts = self.model._meta
        msg = _('The %(name)s "%(obj)s" was changed successfully.') % {
            "name": opts.verbose_name,
            "obj": obj,
        }
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(
            reverse("admin:astrophotography_meteorsmainpageconfig_change", args=[obj.pk])
        )

    def response_add(self, request, obj, post_url_continue=None):
        opts = self.model._meta
        msg = _('The %(name)s "%(obj)s" was added successfully.') % {
            "name": opts.verbose_name,
            "obj": obj,
        }
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(
            reverse("admin:astrophotography_meteorsmainpageconfig_change", args=[obj.pk])
        )

    def changelist_view(self, request, extra_context=None):
        """
        Redirects the changelist view directly to the singleton instance's change view
        (or add view if none exists), enforcing the singleton UX.
        """
        obj = self.model.objects.first()
        if obj:
            return HttpResponseRedirect(
                reverse("admin:astrophotography_meteorsmainpageconfig_change", args=[obj.pk])
            )
        return HttpResponseRedirect(reverse("admin:astrophotography_meteorsmainpageconfig_add"))
