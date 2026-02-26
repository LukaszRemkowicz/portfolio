import calendar
import logging
import uuid
from datetime import date as dt_date
from typing import Any, Optional

import sentry_sdk
from django_ckeditor_5.fields import CKEditor5Field
from django_countries.fields import CountryField
from model_utils import FieldTracker
from parler.managers import TranslatableManager, TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from psycopg2.extras import DateRange as PG_DateRange

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import translation
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from common.constants import FALLBACK_URL_SLUG
from core.models import BaseImage, SingletonModel
from translation.mixins import AutomatedTranslationModelMixin
from translation.services import TranslationService

from .constants import CELESTIAL_OBJECT_CHOICES, MeteorDefaults

logger = logging.getLogger(__name__)


class Place(AutomatedTranslationModelMixin, TranslatableModel):
    objects: TranslatableManager = TranslatableManager()

    # Translation trigger fields
    translation_service_method = "translate_place"
    translation_trigger_fields = ["name"]

    translations = TranslatedFields(
        name=models.CharField(
            verbose_name=_("Name"),
            max_length=100,
            blank=True,
        ),
    )
    country = CountryField(
        verbose_name=_("Country"),
        null=True,
        blank=True,
        help_text=_(
            "Required for non-region places. Leave blank for multi-country regions "
            "(e.g. Scandinavia which spans Norway, Sweden and Finland)."
        ),
    )
    is_region = models.BooleanField(
        default=False,
        verbose_name=_("Is Region"),
        help_text=_(
            "Mark this place as a broad region (e.g. Hawaii, Scandinavia). "
            "Set sub_places to restrict image filtering to specific sub-places. "
            "Country is not required for multi-country regions."
        ),
    )
    sub_places = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        verbose_name=_("Sub-Places"),
        help_text=_(
            "For regions: explicitly list the sub-places that belong to this region "
            "(e.g. Hawaii → Oahu, Big Island; Scandinavia → Norway, Sweden, Finland). "
            "Leave empty to fall back to all places in the same country."
        ),
        related_name="parent_regions",
    )

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        ordering = ["pk"]

    def clean(self):
        """Custom uniqueness validation for Place names."""
        super().clean()
        lang = self.get_current_language()
        current_name = self.safe_translation_getter("name", language_code=lang)

        if current_name:
            # Check for existing Place with same name in same language
            duplicates = self.__class__.objects.translated(lang, name=current_name)
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)

            if duplicates.exists():
                raise ValidationError(
                    {"name": _("Place Translation with this Language and Name already exists.")}
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self.trigger_translations()

    def __str__(self) -> str:
        default_lang = settings.DEFAULT_APP_LANGUAGE
        country_name = ""
        with translation.override(default_lang):
            if self.country:
                country_name = self.country.name
        return self.safe_translation_getter("name", any_language=True) or country_name


class Tag(AutomatedTranslationModelMixin, TranslatableModel, models.Model):
    translation_service_method = "translate_parler_tag"
    translation_trigger_fields = ["name"]
    translations = TranslatedFields(
        name=models.CharField(verbose_name=_("Name"), max_length=100, blank=True),
        slug=models.SlugField(
            verbose_name=_("Slug"),
            max_length=100,
            allow_unicode=True,
        ),
    )

    objects = TranslatableManager()

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def clean(self):
        """Enforce that the name is required for the default language."""
        super().clean()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        name = self.safe_translation_getter("name", language_code=default_lang)
        if not name:
            raise ValidationError({"name": _("This field is required for the default language.")})

        # Check for slug uniqueness manually and map error to 'name'
        # to prevent "TagForm has no field named 'slug'" crashes.
        current_name = self.safe_translation_getter("name")
        if current_name:
            proposed_slug = slugify(current_name, allow_unicode=True)
            # Find any other tag that already has this slug in its translation
            duplicates = Tag.objects.filter(translations__slug=proposed_slug)
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                raise ValidationError({"name": _("A tag with this name/slug already exists.")})

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True) or f"Tag {self.pk}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate slug from translated name (auto-sync)
        source = self.safe_translation_getter("name")
        if source:
            self.slug = slugify(source, allow_unicode=True)
        super().save(*args, **kwargs)
        self.trigger_translations()


class AbstractEquipmentModel(models.Model):
    model = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Model"),
        help_text=_("The model identifiers or name of the equipment."),
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.model


class Camera(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Camera")
        verbose_name_plural = _("Cameras")


class Lens(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Lens")
        verbose_name_plural = _("Lenses")


class Telescope(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Telescope")
        verbose_name_plural = _("Telescopes")


class Tracker(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Tracker")
        verbose_name_plural = _("Trackers")


class Tripod(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Tripod")
        verbose_name_plural = _("Tripods")


class AstroImageQuerySet(TranslatableQuerySet):
    """Custom queryset for AstroImage model."""

    def latest(self):
        """Returns the 9 most recent images."""
        return self.order_by("-capture_date", "-created_at")[:9]


class AstroImage(AutomatedTranslationModelMixin, BaseImage):
    """Model for astrophotography images"""

    # Track changes to the 'path' field (inherited from BaseImage)
    path_tracker = FieldTracker(fields=["path"])

    # Translation trigger fields
    translation_service_method = "translate_astro_image"
    translation_trigger_fields = ["name", "description", "exposure_details", "processing_details"]

    capture_date = models.DateField(
        verbose_name=_("Capture Date"), help_text=_("The date when the photo was taken.")
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Place/City"),
        help_text=_("Specific city or region (e.g. Hawaii, Tenerife)."),
    )
    telescope = models.ManyToManyField(
        Telescope,
        blank=True,
        verbose_name=_("Telescope"),
        help_text=_("Telescope model and specifications"),
    )
    camera = models.ManyToManyField(
        Camera,
        blank=True,
        verbose_name=_("Camera"),
        help_text=_("Camera model and specifications"),
    )
    tracker = models.ManyToManyField(
        Tracker,
        blank=True,
        verbose_name=_("Tracker/Mount"),
        help_text=_("Star tracker or mount model"),
    )
    tripod = models.ManyToManyField(
        Tripod,
        blank=True,
        verbose_name=_("Tripod"),
        help_text=_("Tripod model"),
    )
    lens = models.ManyToManyField(
        Lens,
        blank=True,
        verbose_name=_("Lens"),
        help_text=_("Lens model and focal length"),
    )
    translations = TranslatedFields(
        name=models.CharField(
            max_length=255,
            verbose_name=_("Name"),
            help_text=_("A descriptive name for this image."),
            blank=True,
        ),
        description=CKEditor5Field(
            blank=True,
            verbose_name=_("Description"),
            help_text=_("Optional detailed description of the image."),
            config_name="default",
        ),
        exposure_details=CKEditor5Field(
            blank=True,
            config_name="default",
            verbose_name=_("Exposure Details"),
            help_text=_("Technical details of the exposure (gain, sub-exposures, total time)."),
        ),
        processing_details=CKEditor5Field(
            blank=True,
            config_name="default",
            verbose_name=_("Processing Details"),
            help_text=_("Software and techniques used for post-processing."),
        ),
    )

    celestial_object = models.CharField(
        verbose_name=_("Celestial Object"),
        help_text=_("The type of celestial object captured."),
        max_length=50,
        choices=CELESTIAL_OBJECT_CHOICES,
        default="Landscape",
    )
    astrobin_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Astrobin URL"),
        help_text=_("Link to this image on Astrobin (e.g., https://www.astrobin.com/XXXXX/)"),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="images", verbose_name=_("Tags"))
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("SEO friendly URL slug."),
    )
    zoom = models.BooleanField(
        default=False,
        verbose_name=_("Zoom"),
        help_text=_("Allow users to zoom this image in detail mode."),
    )

    class Meta:
        verbose_name = _("Astrophotography Image")
        verbose_name_plural = _("Astrophotography Images")
        ordering = ["-created_at"]

    objects = AstroImageQuerySet.as_manager()

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        if not name:
            for lang in self.get_available_languages():
                name = self.safe_translation_getter("name", language_code=lang)
                if name:
                    break
        return str(name) if name else str(self.id)

    def clean(self):
        """Enforce that the name is required for the default language."""
        super().clean()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        # Use safe_translation_getter to check the current language's name if it's default
        # or explicitly check the default language translation.
        name = self.safe_translation_getter("name", language_code=default_lang)
        if not name:
            raise ValidationError({"name": _("This field is required for the default language.")})

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            # We use the English name (master/fallback) for slug generation
            base_slug = slugify(self.safe_translation_getter("name", any_language=True))
            if not base_slug:
                base_slug = "image"

            self.slug = base_slug
            # If slug already exists, append a short UUID
            if AstroImage.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
        self.trigger_translations()


class MainPageBackgroundImage(AutomatedTranslationModelMixin, BaseImage):
    """Images used as full-page backgrounds on the main portal."""

    path_tracker = FieldTracker(fields=["path"])

    # Translation trigger fields
    translation_service_method = "translate_main_page_background_image"
    translation_trigger_fields = ["name", "description"]

    path = models.ImageField(
        upload_to="backgrounds/",
        verbose_name=_("Image File"),
        help_text=_("The large background image file."),
    )
    translations = TranslatedFields(
        name=models.CharField(
            max_length=255,
            default="Background Image",
            verbose_name=_("Name"),
            help_text=_("Identifier for the background image."),
            blank=True,
        ),
        description=CKEditor5Field(
            blank=True,
            verbose_name=_("Description"),
            help_text=_("Optional detailed description of the image."),
            config_name="default",
        ),
    )

    class Meta:
        verbose_name = _("Main Page Background Image")
        verbose_name_plural = _("Main Page Background Images")
        ordering = ["-created_at"]

    def clean(self):
        """Enforce that the name is required for the default language."""
        super().clean()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        name = self.safe_translation_getter("name", language_code=default_lang)
        if not name:
            raise ValidationError({"name": _("This field is required for the default language.")})

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self.trigger_translations()

    def __str__(self) -> str:
        name = self.safe_translation_getter("name", any_language=True)
        return name or f"Main Page Background Image {self.pk}"


class MainPageLocationQuerySet(TranslatableQuerySet):
    """Custom queryset for MainPageLocation model."""

    def active(self) -> "MainPageLocationQuerySet":
        """Return only active locations."""
        return self.filter(is_active=True)  # type: ignore[no-any-return]

    def with_images(self) -> "MainPageLocationQuerySet":
        """Prefetch related images for efficiency."""
        return self.prefetch_related("images")  # type: ignore[no-any-return]

    def with_place(self) -> "MainPageLocationQuerySet":
        """Select related place for efficiency."""
        return self.select_related("place")  # type: ignore[no-any-return]

    def by_slugs(
        self, country_slug: str, place_slug: str, date_slug: str
    ) -> "MainPageLocationQuerySet":
        """
        Filter locations by country, place, and date slugs.
        """
        qs = self.all()

        # 1. Country filter
        if country_slug != FALLBACK_URL_SLUG:
            qs = qs.filter(country_slug=country_slug)
        else:
            qs = qs.filter(country_slug="")

        # 2. Place filter
        if place_slug != FALLBACK_URL_SLUG:
            qs = qs.filter(place_slug=place_slug)
        else:
            qs = qs.filter(place__isnull=True)

        # 3. Date filter
        if date_slug != FALLBACK_URL_SLUG:
            date_range = MainPageLocation._parse_date_slug(date_slug)
            if date_range:
                qs = qs.filter(adventure_date__overlap=date_range)
            else:
                return self.none()  # type: ignore[no-any-return]

        return qs  # type: ignore[no-any-return]


class MainPageLocation(AutomatedTranslationModelMixin, TranslatableModel):
    # Custom manager with translation support
    objects = MainPageLocationQuerySet.as_manager()

    # Translation trigger fields
    translation_service_method = "translate_main_page_location"
    translation_trigger_fields = ["highlight_name", "highlight_title", "story"]
    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Place/City"),
        help_text=_("Specific city or region (e.g. Hawaii, Tenerife)"),
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active"), help_text=_("Toggle visibility on the homepage.")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def clean(self):
        """Enforce that the highlight_name is required for the default language,
        and validate uniqueness."""
        super().clean()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        name = self.safe_translation_getter("highlight_name", language_code=default_lang)
        if not name:
            raise ValidationError(
                {"highlight_name": _("This field is required for the default language.")}
            )

    adventure_date = DateRangeField(
        verbose_name=_("Adventure Date Range"),
        help_text=_("The date range of the expedition. Required for generating the URL slug."),
        null=False,
        blank=False,
    )

    country_slug = models.SlugField(
        max_length=100,
        verbose_name=_("Country Slug"),
        help_text=_("Auto-generated slug for the country."),
        blank=True,
    )
    place_slug = models.SlugField(
        max_length=100,
        verbose_name=_("Place Slug"),
        help_text=_("Auto-generated slug for the place."),
        null=True,
        blank=True,
    )

    background_image = models.ForeignKey(
        AstroImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Background Image"),
        help_text=_("Optional specific background image for this location's page."),
        related_name="location_backgrounds",
    )
    images = models.ManyToManyField(
        AstroImage,
        blank=True,
        verbose_name=_("Images"),
        help_text=_(
            "Select images to display in the slideshow for this location (filtered by country)."
        ),
        related_name="location_sliders",
    )

    translations = TranslatedFields(
        highlight_name=models.CharField(
            max_length=100,
            verbose_name=_("Highlight Name"),
            help_text=_("Optional custom name for the travel highlight (overrides Country/Place)."),
            null=True,
            blank=True,
        ),
        highlight_title=models.CharField(
            max_length=255,
            verbose_name=_("Highlight Title"),
            help_text=_(
                "Custom title for the highlights page. Description visible for a given "
                "location at the top of the page."
            ),
            null=True,
            blank=True,
        ),
        story=CKEditor5Field(
            verbose_name=_("Story/Blog Text"),
            help_text=_("Optional story or blog text to display above the images."),
            null=True,
            blank=True,
            config_name="default",
        ),
    )

    class Meta:
        verbose_name = _("Main Page Location")
        verbose_name_plural = _("Main Page Locations")
        ordering = ["-adventure_date"]
        constraints = [
            ExclusionConstraint(
                name="exclude_overlapping_adventure_dates",
                expressions=[
                    ("place", "="),
                    ("adventure_date", "&&"),
                ],
                violation_error_message=_(
                    "A travel highlight for this Place with an overlapping "
                    "Date range already exists."
                ),
            )
        ]

    def __str__(self) -> str:
        name = self.safe_translation_getter("highlight_name", any_language=True)
        if not name and self.place:
            name = f"{self.place.country.name} - {self.place.name}"

        status_str = _("Active") if self.is_active else _("Inactive")
        return f"{name or _('Unnamed Location')} ({status_str})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Always keep slugs up to date with the assigned Place.
        if self.place:
            if self.place.is_region or not self.place.country:
                self.country_slug = ""
            else:
                # Handle django-countries Country object
                country_name = getattr(self.place.country, "name", str(self.place.country))
                self.country_slug = slugify(country_name)
            if self.place.name:
                self.place_slug = slugify(self.place.name)
        else:
            self.country_slug = ""
            self.place_slug = ""

        super().save(*args, **kwargs)
        self.trigger_translations()

    # Domain Logic Methods

    def get_full_location(self, language_code: str = "en") -> str:
        """Get full location string (place, country)."""
        place_name = TranslationService.get_translation(self, "highlight_name", language_code)
        if not place_name:
            if language_code == settings.DEFAULT_APP_LANGUAGE and self.place:
                place_name = self.place.name
            else:
                return ""

        country_name = self.place.country.name if self.place else "Unknown"
        return f"{place_name}, {country_name}"

    def get_story_preview(self, language_code: str = "en", max_length: int = 150) -> str:
        """Get truncated story for previews."""
        story = TranslationService.get_translation(self, "story", language_code)
        if len(story) > max_length:
            return story[:max_length].rsplit(" ", 1)[0] + "..."
        return story

    @property
    def date_slug(self) -> str:
        """
        Returns a URL-safe adventure date string like 'jan2026'.
        Always uses English month abbreviations for stable URLs regardless of UI language.
        Raises AttributeError when no adventure_date is set.
        """
        if not self.adventure_date or not self.adventure_date.lower:
            msg = (
                f"MainPageLocation (ID: {self.pk}) has no adventure_date set. "
                "Date range is required for URL generation."
            )
            logger.error(msg)
            sentry_sdk.capture_message(msg, level="error")
            raise AttributeError(msg)
        return self.adventure_date.lower.strftime("%b%Y").lower()  # type: ignore[no-any-return]

    @property
    def adventure_date_raw(self) -> str:
        """
        Returns the lower boundary of the adventure date in ISO format
        for frontend slug generation.
        Raises AttributeError when no adventure_date is set.
        """
        if not self.adventure_date or not self.adventure_date.lower:
            msg = (
                f"MainPageLocation (ID: {self.pk}) has no adventure_date set. "
                "Date range is required for URL generation."
            )
            logger.error(msg)
            sentry_sdk.capture_message(msg, level="error")
            raise AttributeError(msg)
        return self.adventure_date.lower.isoformat()  # type: ignore[no-any-return]

    @staticmethod
    def _parse_date_slug(date_slug: str) -> Optional[PG_DateRange]:
        """
        Parses a date slug like 'jan2026' into a psycopg2 DateRange.
        Returns None if parsing fails.
        """
        try:
            # Example: 'jan2026'
            month_str = date_slug[:3].lower()
            year_str = date_slug[3:]

            # Use month_abbr for 3-letter abbreviations ('jan', 'feb', etc.)
            months = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
            month = months.get(month_str)
            year = int(year_str)

            if not month:
                return None

            first_day = dt_date(year, month, 1)
            if month == 12:
                next_month_start = dt_date(year + 1, 1, 1)
            else:
                next_month_start = dt_date(year, month + 1, 1)

            return PG_DateRange(first_day, next_month_start, bounds="[)")
        except (ValueError, IndexError, KeyError):
            return None


class MeteorsMainPageConfig(SingletonModel):
    random_stars_shooting = models.BooleanField(
        default=True,
        verbose_name=_("Random Shooting Stars"),
        help_text=_(
            "If enabled, shooting stars will have randomized flight angles (0-360°). "
            "If disabled, they will follow a fixed -45° diagonal path."
        ),
    )
    bolid_chance = models.FloatField(
        default=0.1,
        verbose_name=_("Bolid Chance"),
        help_text=_(
            "The probability (0.0 to 1.0) of a regular shooting star being a 'bolid' (fireball). "
            "0.1 means a 10% chance."
        ),
    )
    bolid_interval = models.IntegerField(
        default=60,
        verbose_name=_("Bolid Minimum Interval"),
        help_text=_(
            "Minimum wait time (in seconds) between consecutive bolid sightings to prevent "
            "clusters. "
            "Note: Bolid speed is calculated as Path Distance / Duration. "
            "(Smaller duration + Larger distance = High speed)."
        ),
    )
    star_path_range = models.JSONField(
        default=MeteorDefaults.star_path,
        verbose_name=_("Star Path Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "regular star in pixels. Example: [50, 500]"
        ),
    )
    bolid_path_range = models.JSONField(
        default=MeteorDefaults.bolid_path,
        verbose_name=_("Bolid Path Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "bolid in pixels. Example: [50, 500]"
        ),
    )
    star_streak_range = models.JSONField(
        default=MeteorDefaults.star_streak,
        verbose_name=_("Star Streak Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of a "
            "regular star. Example: [100, 200]"
        ),
    )
    bolid_streak_range = models.JSONField(
        default=MeteorDefaults.bolid_streak,
        verbose_name=_("Bolid Streak Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of "
            "a bolid. Example: [20, 100]"
        ),
    )
    star_duration_range = models.JSONField(
        default=MeteorDefaults.star_duration,
        verbose_name=_("Star Duration Range (s)"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a regular star. "
            "Example: [0.4, 1.2]"
        ),
    )
    bolid_duration_range = models.JSONField(
        default=MeteorDefaults.bolid_duration,
        verbose_name=_("Bolid Duration Range (s)"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a bolid. "
            "Example: [0.4, 0.9]"
        ),
    )
    star_opacity_range = models.JSONField(
        default=MeteorDefaults.star_opacity,
        verbose_name=_("Star Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for regular star brightness. "
            "Example: [0.4, 0.8]"
        ),
    )
    bolid_opacity_range = models.JSONField(
        default=MeteorDefaults.bolid_opacity,
        verbose_name=_("Bolid Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for bolid brightness. "
            "Example: [0.7, 1.0]"
        ),
    )
    smoke_opacity_range = models.JSONField(
        default=MeteorDefaults.smoke_opacity,
        verbose_name=_("Smoke Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for the smoke trail of a bolid. "
            "Example: [0.5, 0.8]"
        ),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Meteors Main Page Configuration")
        verbose_name_plural = _("Meteors Main Page Configuration")

    def __str__(self) -> str:
        return str(_("Meteors Configuration"))
