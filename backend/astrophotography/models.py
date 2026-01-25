# backend/astrophotography/models.py
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from django_countries.fields import CountryField
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core.models import BaseImage, SingletonModel


def default_star_path():
    return [50, 500]


def default_bolid_path():
    return [50, 500]


def default_star_streak():
    return [100, 200]


def default_bolid_streak():
    return [20, 100]


def default_star_opacity():
    return [0.4, 0.8]


def default_bolid_opacity():
    return [0.7, 1.0]


def default_smoke_opacity():
    return [0.5, 0.8]


def default_star_duration():
    return [0.4, 1.2]


def default_bolid_duration():
    return [0.4, 0.9]


CelestialObjectChoices = [
    ("Landscape", _("Landscape")),
    ("Deep Sky", _("Deep Sky")),
    ("Startrails", _("Startrails")),
    ("Solar System", _("Solar System")),
    ("Milky Way", _("Milky Way")),
    ("Northern Lights", _("Northern Lights")),
]


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class AbstractEquipmentModel(models.Model):
    model = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Model"),
        help_text=_("The model identifiers or name of the equipment."),
    )

    def __str__(self) -> str:
        return self.model

    class Meta:
        abstract = True
        ordering = ["model"]


class Place(models.Model):
    name = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("Name"),
        help_text=_("The name of the specific place or city."),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        ordering = ["name"]


class Telescope(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Telescope")
        verbose_name_plural = _("Telescopes")


class Camera(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Camera")
        verbose_name_plural = _("Cameras")


class Lens(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Lens")
        verbose_name_plural = _("Lenses")


class Tracker(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Tracker")
        verbose_name_plural = _("Trackers")


class Tripod(AbstractEquipmentModel):
    class Meta:
        verbose_name = _("Tripod")
        verbose_name_plural = _("Tripods")


class AstroImage(BaseImage):
    """Model for astrophotography images"""

    capture_date = models.DateField(
        verbose_name=_("Capture Date"), help_text=_("The date when the photo was taken.")
    )
    location = CountryField(
        blank=True,
        null=True,
        verbose_name=_("Country"),
        help_text=_("The country where the photo was taken."),
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
    exposure_details = models.TextField(
        blank=True,
        verbose_name=_("Exposure Details"),
        help_text=_("Technical details of the exposure (gain, sub-exposures, total time)."),
    )
    processing_details = models.TextField(
        blank=True,
        verbose_name=_("Processing Details"),
        help_text=_("Software and techniques used for post-processing."),
    )
    celestial_object = models.CharField(
        max_length=50,
        choices=CelestialObjectChoices,
        verbose_name=_("Celestial Object"),
        help_text=_("The type of celestial object captured."),
    )
    astrobin_url = models.URLField(
        max_length=200,
        blank=True,
        verbose_name=_("Astrobin URL"),
        help_text=_("Link to this image on Astrobin (e.g., https://www.astrobin.com/XXXXX/)"),
    )
    tags = TaggableManager(
        through=UUIDTaggedItem, verbose_name=_("Tags"), help_text=_("Relevant tags for the image.")
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.capture_date})" if self.capture_date else self.name

    class Meta:
        verbose_name = _("Astrophotography Image")
        verbose_name_plural = _("Astrophotography Images")
        ordering = ["-created_at"]


class MainPageLocation(models.Model):
    """Model to manage which images appear in the travel section for a specific location"""

    country = CountryField(
        verbose_name=_("Country"), help_text=_("The country for this travel highlights slider.")
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Place/City"),
        help_text=_("Specific city or region (e.g. Hawaii, Tenerife)"),
    )
    images = models.ManyToManyField(
        AstroImage,
        blank=True,
        related_name="location_sliders",
        verbose_name=_("Images"),
        help_text=_(
            "Select images to display in the slideshow for this location (filtered by country)."
        ),
    )
    is_active = models.BooleanField(
        default=True, verbose_name=_("Is Active"), help_text=_("Toggle visibility on the homepage.")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    highlight_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Highlight Name"),
        help_text=_("Optional custom name for the travel highlight (overrides Country/Place)."),
    )
    adventure_date = DateRangeField(
        blank=True,
        null=True,
        verbose_name=_("Adventure Date Range"),
        help_text=_("The date range of the expedition."),
    )
    country_slug = models.SlugField(
        max_length=100,
        blank=True,
        verbose_name=_("Country Slug"),
        help_text=_("Auto-generated slug for the country."),
    )
    place_slug = models.SlugField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Place Slug"),
        help_text=_("Auto-generated slug for the place."),
    )
    story = CKEditor5Field(
        blank=True,
        null=True,
        verbose_name=_("Story/Blog Text"),
        help_text=_("Optional story or blog text to display above the images."),
        config_name="default",
    )

    background_image = models.ForeignKey(
        "AstroImage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_backgrounds",
        verbose_name=_("Background Image"),
        help_text=_("Optional specific background image for this location's page."),
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.country:
            self.country_slug = slugify(self.country.name)

        if self.place:
            self.place_slug = slugify(self.place.name)
        else:
            self.place_slug = None

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.highlight_name:
            return f"{self.highlight_name} ({'Active' if self.is_active else 'Inactive'})"

        location = f"{self.country.name}"
        if self.place:
            location += f" ({self.place})"
        return f"Location: {location} ({'Active' if self.is_active else 'Inactive'})"

    class Meta:
        verbose_name = _("Main Page Location")
        verbose_name_plural = _("Main Page Locations")
        ordering = ["-adventure_date"]


class MainPageBackgroundImage(BaseImage):
    """Model for the main page background image"""

    # Override fields with appropriate defaults
    name = models.CharField(
        max_length=255,
        default="Background Image",
        verbose_name=_("Name"),
        help_text=_("Identifier for the background image."),
    )
    path = models.ImageField(
        upload_to="backgrounds/",
        verbose_name=_("Image File"),
        help_text=_("The large background image file."),
    )

    class Meta:
        verbose_name = _("Main Page Background Image")
        verbose_name_plural = _("Main Page Background Images")
        ordering = ["-created_at"]


class MeteorsMainPageConfig(SingletonModel):
    """Global configuration for shooting stars (meteors) on the homepage"""

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
            "The minimum wait time (in seconds) between two bolid spawns to prevent cluster "
            "sightings. Duration ranges (in seconds) on screen depends on path distance. "
            "Speed = PathDistance / Duration. "
            "- Smaller duration + Larger distance = High speed. "
            "- Larger duration + Smaller distance = Low speed."
        ),
    )
    star_path_range = models.JSONField(
        default=default_star_path,
        verbose_name=_("Star Path Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "regular star in pixels. Example: [50, 500]"
        ),
    )
    bolid_path_range = models.JSONField(
        default=default_bolid_path,
        verbose_name=_("Bolid Path Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the travel distance of a "
            "bolid in pixels. Example: [50, 500]"
        ),
    )
    star_streak_range = models.JSONField(
        default=default_star_streak,
        verbose_name=_("Star Streak Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of a "
            "regular star. Example: [100, 200]"
        ),
    )
    bolid_streak_range = models.JSONField(
        default=default_bolid_streak,
        verbose_name=_("Bolid Streak Range (px)"),
        help_text=_(
            "A list of two integers [min, max] representing the visual length (streak) of "
            "a bolid. Example: [20, 100]"
        ),
    )
    star_duration_range = models.JSONField(
        default=default_star_duration,
        verbose_name=_("Star Duration Range (s)"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a regular star. "
            "Example: [0.4, 1.2]"
        ),
    )
    bolid_duration_range = models.JSONField(
        default=default_bolid_duration,
        verbose_name=_("Bolid Duration Range (s)"),
        help_text=_(
            "A list of two floats [min, max] representing the duration (speed) of a bolid. "
            "Example: [0.4, 0.9]"
        ),
    )
    star_opacity_range = models.JSONField(
        default=default_star_opacity,
        verbose_name=_("Star Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for regular star brightness. "
            "Example: [0.4, 0.8]"
        ),
    )
    bolid_opacity_range = models.JSONField(
        default=default_bolid_opacity,
        verbose_name=_("Bolid Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for bolid brightness. "
            "Example: [0.7, 1.0]"
        ),
    )
    smoke_opacity_range = models.JSONField(
        default=default_smoke_opacity,
        verbose_name=_("Smoke Opacity Range"),
        help_text=_(
            "A list of two floats [min, max] between 0.0 and 1.0 for the smoke trail of a bolid. "
            "Example: [0.5, 0.8]"
        ),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self) -> str:
        return f"Meteors Config (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = _("Meteors Main Page Configuration")
        verbose_name_plural = _("Meteors Main Page Configuration")
