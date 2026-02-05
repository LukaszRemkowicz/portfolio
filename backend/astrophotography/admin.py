import logging

from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.postgres.forms import RangeWidget
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.mixins import AutomatedTranslationMixin, DynamicParlerStyleMixin
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
    Tag,
    Telescope,
    Tracker,
    Tripod,
)

logger = logging.getLogger(__name__)


@admin.register(Place)
class PlaceAdmin(AutomatedTranslationMixin, DynamicParlerStyleMixin, TranslatableAdmin):
    """
    Admin configuration for geographical places.
    Supports automated translation of place names into multiple languages.
    """

    translation_service_method = "translate_place"
    translation_trigger_fields = ["name"]

    list_display = ("id", "get_name", "country")
    list_display_links = ("get_name",)
    search_fields = ("translations__name", "country")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.distinct()

    def get_name(self, obj):
        """Returns the string representation of the place."""
        return str(obj)

    get_name.short_description = _("Name")


# Taggit admin unregistration removed as the library is being uninstalled.


@admin.register(Tag)
class TagAdmin(AutomatedTranslationMixin, DynamicParlerStyleMixin, TranslatableAdmin):
    translation_service_method = "translate_parler_tag"
    translation_trigger_fields = ["name"]

    list_display = ("get_name", "slug", "id")
    list_display_links = ("get_name",)
    search_fields = ("translations__name", "slug")
    readonly_fields = ("slug",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                )
            },
        ),
    )

    def get_translation_kwargs(self, obj, form, change, should_trigger):
        return {"force": should_trigger}

    def get_name(self, obj):
        return str(obj)

    get_name.short_description = _("Name")


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
class AstroImageAdmin(AutomatedTranslationMixin, DynamicParlerStyleMixin, TranslatableAdmin):
    """
    Main admin for Astrophotography images.
    Complex logic includes:
    - Dynamic fieldsets (hiding technical fields in non-default languages)
    - Automated GPT-powered translations on save
    - Dynamic filtering of equipment and locations
    """

    translation_service_method = "translate_astro_image"
    translation_trigger_fields = ["name", "description", "exposure_details", "processing_details"]

    form = AstroImageForm
    list_display = ("get_name", "capture_date", "place", "has_thumbnail", "tag_list")
    list_display_links = ("get_name",)
    list_filter = ("celestial_object", "tags")

    def get_name(self, obj):
        return str(obj)

    get_name.short_description = _("Name")
    search_fields = (
        "translations__name",
        "translations__description",
        "place__translations__name",
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
                    "zoom",
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
                "fields": ("place",),
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

    def get_fieldsets(self, request, obj=None):
        """
        Dynamically hide non-translatable fields when editing a secondary language.
        """
        # Determine the current language code from the request
        current_language = request.GET.get("language")

        # Get default language (fallback). Hardcoded 'en' or fetch from settings.
        # Ideally, use settings.PARLER_LANGUAGES['default']['fallback']
        default_language = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", "en")

        # If we are editing a specific language that is NOT the default, hide shared fields
        if current_language and current_language != default_language:
            return (
                (
                    None,
                    {
                        "fields": (
                            "name",
                            "description",
                        )
                    },
                ),
                (
                    _("Technical Details"),
                    {
                        "fields": ("exposure_details", "processing_details"),
                        "classes": ("collapse",),
                    },
                ),
                # You might want to show a read-only sections for context, but user asked to HIDE.
            )

        return super().get_fieldsets(request, obj)

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
class MainPageBackgroundImageAdmin(DynamicParlerStyleMixin, TranslatableAdmin):
    list_display = ("get_name", "path", "created_at")
    list_display_links = ("get_name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "description", "path")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_name(self, obj):
        return str(obj)

    get_name.short_description = _("Name")


class MainPageLocationForm(TranslatableModelForm):
    images = forms.ModelMultipleChoiceField(
        queryset=AstroImage.objects.all(),
        widget=ThemedSelect2MultipleWidget(),
        required=False,
        label=_("Images"),
        help_text=_(
            "Select images to display in the slideshow for this location " "(filtered by place)."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fix duplicate places in dropdown by clearing ordering
        if "place" in self.fields:
            self.fields["place"].queryset = Place.objects.order_by("pk").distinct()

        self._apply_dynamic_filtering()

    def _apply_dynamic_filtering(self):  # noqa: C901
        """
        Dynamically filter the available images based on the selected place.
        """
        # Dynamic filtering for images field
        if self.instance.pk:
            # Edit mode
            qs = AstroImage.objects.filter(place=self.instance.place)
            images_field = self.fields.get("images")
            if isinstance(images_field, forms.ModelChoiceField):
                images_field.queryset = qs

            bg_image_field = self.fields.get("background_image")
            if isinstance(bg_image_field, forms.ModelChoiceField):
                bg_image_field.queryset = qs

            if not qs.exists():
                self.fields["images"].widget = ReadOnlyMessageWidget(
                    message=_("No matching items found for this place.")
                )
        else:
            # Creation mode
            # Logic simplified for now
            pass

    class Meta:
        model = MainPageLocation
        fields = "__all__"
        widgets = {
            # country widget removed
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

    def clean_place(self):
        place = self.cleaned_data.get("place")
        if not place:
            place_name = self.data.get("place")
            if place_name:
                # Use translated name lookup? Or just simple name for now
                # Place name is translatable now. get_or_create by name kwarg relies on Parler
                # helping, or we need to use translations__name.
                # For simplicity in admin form logic, try direct lookup which Parler might intercept
                # or use safe lookup
                # Parler models manager handles .get(name=...) by querying translations.
                place, _ = Place.objects.get_or_create(name=place_name)
        elif isinstance(place, str):
            place, _ = Place.objects.get_or_create(name=place)
        return place


@admin.register(MainPageLocation)
class MainPageLocationAdmin(AutomatedTranslationMixin, DynamicParlerStyleMixin, TranslatableAdmin):
    translation_service_method = "translate_main_page_location"
    translation_trigger_fields = ["highlight_name", "story"]

    form = MainPageLocationForm
    list_display = ("pk", "place", "highlight_name", "is_active")
    list_display_links = ("pk", "place")
    list_filter = ("is_active", "place")
    search_fields = ("place__translations__name", "translations__highlight_name")
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
