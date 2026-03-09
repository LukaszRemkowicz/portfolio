import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from astrophotography.services import GalleryQueryService
from core.widgets import (
    ReadOnlyMessageWidget,
    ThemedRangeWidget,
    ThemedSelect2MultipleWidget,
    ThemedSelect2Widget,
)
from translation.mixins import (
    AutomatedTranslationAdminMixin,
    DynamicParlerStyleMixin,
    TranslationStatusMixin,
)

from .admin_mixins import SecureAdminSidebarPreviewMixin
from .forms import (
    AstroImageForm,
    MainPageBackgroundImageForm,
    MeteorsMainPageConfigForm,
    PlaceAdminForm,
    TagAdminForm,
)
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


class RegionFilter(admin.SimpleListFilter):
    """
    Sidebar filter for PlaceAdmin that lists each region by name.
    Selecting a region shows all its sub-places.
    Selecting 'Regions only' shows all region-type places.
    """

    title = _("Region")
    parameter_name = "region"

    def lookups(self, request, model_admin):

        regions = Place.objects.filter(is_region=True).order_by("pk")

        choices: list[tuple[str, Any]] = [("__regions__", _("Regions only"))]
        for region in regions:
            choices.append((str(region.pk), str(region)))
        return choices

    def queryset(self, request, queryset):
        value = self.value()
        if value == "__regions__":
            return queryset.filter(is_region=True)
        if value:
            try:
                region = Place.objects.get(pk=value, is_region=True)
                return queryset.filter(parent_regions=region)
            except (Place.DoesNotExist, ValueError):
                pass
        return queryset


class BaseTranslatableAdmin(
    AutomatedTranslationAdminMixin,
    TranslationStatusMixin,
    DynamicParlerStyleMixin,
    TranslatableAdmin,
):
    """
    Base admin for translatable models in the astrophotography module.
    Shared complex logic includes:
    - Automated GPT-powered translations on save (via AutomatedTranslationMixin)
    - Dynamic Parler-style UI synchronization (via DynamicParlerStyleMixin)
    - Translation status tracking and verification (via TranslationStatusMixin)
    """

    pass


@admin.register(Place)
class PlaceAdmin(BaseTranslatableAdmin):
    """Admin configuration for geographical places."""

    fields = ("is_region", "name", "country", "sub_places")
    form = PlaceAdminForm

    list_display = ("id", "get_name", "country", "is_region", "get_regions")
    list_display_links = ("get_name",)
    search_fields = ("translations__name", "country")
    list_filter = (RegionFilter,)

    class Media:
        js = ("core/js/place_admin.js",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.distinct()  # type: ignore[no-any-return]

    @admin.display(description=_("Name"))
    def get_name(self, obj: Place) -> str:
        """Returns the string representation of the place."""
        return str(obj)

    @admin.display(description=_("Belongs to Regions"))
    def get_regions(self, obj: Place) -> str:
        """Returns comma-separated list of regions this place belongs to."""
        regions = obj.parent_regions.all()
        if not regions:
            return "-"
        return ", ".join(str(region) for region in regions)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        """
        Switch active language to the one currently being edited (via Parler tab)
        so that shared fields like CountryField display localized choices.
        """
        lang_code = request.GET.get("language")
        if lang_code:
            translation.activate(lang_code)
            if hasattr(request, "LANGUAGE_CODE"):
                request.LANGUAGE_CODE = lang_code

        return super().changeform_view(  # type: ignore[no-any-return]
            request, object_id, form_url, extra_context
        )


@admin.register(Tag)
class TagAdmin(BaseTranslatableAdmin):
    """Admin configuration for image tags."""

    form = TagAdminForm
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

    @admin.display(description=_("Name"))
    def get_name(self, obj: Tag) -> str:
        return str(obj)


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
class AstroImageAdmin(SecureAdminSidebarPreviewMixin, BaseTranslatableAdmin):
    """
    Main admin for astrophotography captures and related data.
    Unique complex logic:
    - Dynamic fieldsets mapping (hiding technical fields in non-default languages)
    - Dynamic filtering of equipment and locations
    - Custom sidebar image preview
    """

    change_form_template = "admin/astrophotography/secure_media_change_form.html"
    form = AstroImageForm
    list_display = ("get_name", "capture_date", "place", "has_thumbnail", "tag_list")
    list_display_links = ("get_name",)
    list_filter = ("celestial_object", "tags")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related("place").prefetch_related("tags")  # type: ignore[no-any-return]

    @admin.display(description=_("Name"))
    def get_name(self, obj: AstroImage) -> str:
        name = obj.safe_translation_getter("name", any_language=True)
        if not name:
            for lang in obj.get_available_languages():
                name = obj.safe_translation_getter("name", language_code=lang)
                if name:
                    break
        return str(name) if name else str(obj.id)

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

    readonly_fields = ("created_at", "updated_at", "thumbnail")

    ordering = ("-capture_date", "-created_at")

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

    def get_fieldsets(
        self, request: HttpRequest, obj: Optional[AstroImage] = None
    ) -> List[Union[Tuple[Optional[str], Dict[str, Any]], Any]]:
        """
        Dynamically hide non-translatable fields when editing a secondary language.
        """
        # Determine the current language code from the request
        current_language = request.GET.get("language")

        # Get default language (fallback). Hardcoded 'en' or fetch from settings.
        # Ideally, use settings.PARLER_LANGUAGES['default']['fallback']
        default_language = settings.DEFAULT_APP_LANGUAGE

        # If we are editing a specific language that is NOT the default, hide shared fields
        if current_language and current_language != default_language:
            return [
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
            ]

        return super().get_fieldsets(request, obj)  # type: ignore[no-any-return]

    def tag_list(self, obj: AstroImage) -> str:
        return ", ".join(tag.name for tag in obj.tags.all())

    ordering = ("-capture_date", "-created_at")

    @admin.display(boolean=True, description="Has Thumbnail")
    def has_thumbnail(self, obj: AstroImage) -> bool:
        return bool(obj.thumbnail)

    secure_preview_url_name = "admin-astroimage-secure-media"


@admin.register(MainPageBackgroundImage)
class MainPageBackgroundImageAdmin(BaseTranslatableAdmin):
    """
    Admin for main page background images.
    Features:
    - Dynamic Parler-style UI synchronization for translations
    """

    form = MainPageBackgroundImageForm

    list_display = ("get_name", "path", "created_at")
    list_display_links = ("get_name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "description", "path")}),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description=_("Name"))
    def get_name(self, obj: MainPageBackgroundImage) -> str:
        return str(obj)


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

        - No place (explore_tour): all images from that country (via country_slug)
        - Exact place (not a region): only images from that specific place
        - Region with sub_places defined: only images from the listed sub-places
        - Region with no sub_places: fall back to all images in the same country
        """
        if self.instance.pk:
            place = self.instance.place

            if place is None:
                # Fallback for country-wide tours: find the ISO code and show all images
                # from that country.

                maps = GalleryQueryService._get_country_maps()
                iso_code = maps["code_map"].get(self.instance.country_slug) or maps[
                    "country_map"
                ].get(self.instance.country_slug)
                if iso_code:
                    qs = AstroImage.objects.filter(place__country=iso_code)
                else:
                    qs = AstroImage.objects.filter(
                        place__country__icontains=self.instance.country_slug
                    )
            elif place.is_region:
                sub_places = place.sub_places.all()
                if sub_places.exists():
                    countries = {str(sp.country) for sp in sub_places if sp.country}
                    if len(countries) > 1:
                        # Multi-country region (e.g. Scandinavia → Norway, Sweden, Finland):
                        # filter by country so images from any city in those countries appear.
                        qs = AstroImage.objects.filter(place__country__in=countries)
                    else:
                        # Single-country region (e.g. Hawaii → Oahu, Big Island):
                        # filter by the exact sub-places to avoid including unrelated places
                        # in the same country (e.g. Arkansas).
                        qs = AstroImage.objects.filter(place__in=sub_places)
                else:
                    # No sub_places configured: fall back to country-wide (backward compat)
                    qs = AstroImage.objects.filter(place__country=place.country)
            else:
                qs = AstroImage.objects.filter(place=place)

            images_field = self.fields.get("images")
            if isinstance(images_field, forms.ModelChoiceField):
                images_field.queryset = qs

            bg_image_field = self.fields.get("background_image")
            if isinstance(bg_image_field, forms.ModelChoiceField):
                bg_image_field.queryset = qs

            if not qs.exists():
                self.fields["images"].widget = ReadOnlyMessageWidget(
                    message=_(
                        "No matching items found for this place. "
                        "Check the place assignment on your images."
                    )
                )
        else:
            # Creation mode — no place selected yet, show all images
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
            "adventure_date": ThemedRangeWidget(
                base_widget=forms.DateInput(
                    format="%Y-%m-%d", attrs={"type": "date", "onclick": "this.showPicker()"}
                ),
                placeholder_min=_("Start Date"),
                placeholder_max=_("End Date"),
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
class MainPageLocationAdmin(BaseTranslatableAdmin):
    """
    Admin for main page highlight locations and stories.
    Unique complex logic:
    - Selection of related AstroImages filtered by place
    - Synchronized ID-based URL slugs for SEO
    """

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
                "core/css/admin_expandable.css",
            )
        }
        js = ("core/js/admin_expandable_fields.js",)

    fields = (
        "highlight_name",
        "highlight_title",
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

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        extra_context = extra_context or {}
        # Hide "Save and add another" button when editing (only show when adding)
        if object_id:
            extra_context["show_save_and_add_another"] = False

        return super().changeform_view(  # type: ignore[no-any-return]
            request, object_id, form_url, extra_context
        )


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

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only allow adding if no instance exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[MeteorsMainPageConfig] = None
    ) -> bool:
        # Prevent deletion of the last configuration
        if self.model.objects.count() <= 1:
            return False
        return super().has_delete_permission(request, obj)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: Optional[str] = None,
        form_url: str = "",
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> HttpResponse:
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def response_change(self, request: HttpRequest, obj: MeteorsMainPageConfig) -> HttpResponse:
        opts = self.model._meta
        msg = _('The %(name)s "%(obj)s" was changed successfully.') % {
            "name": opts.verbose_name,
            "obj": obj,
        }
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(
            reverse("admin:astrophotography_meteorsmainpageconfig_change", args=[obj.pk])
        )

    def response_add(
        self,
        request: HttpRequest,
        obj: MeteorsMainPageConfig,
        post_url_continue: Optional[str] = None,
    ) -> HttpResponse:
        opts = self.model._meta
        msg = _('The %(name)s "%(obj)s" was added successfully.') % {
            "name": opts.verbose_name,
            "obj": obj,
        }
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(
            reverse("admin:astrophotography_meteorsmainpageconfig_change", args=[obj.pk])
        )

    def changelist_view(
        self, request: HttpRequest, extra_context: Optional[Dict[str, Any]] = None
    ) -> HttpResponse:
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
