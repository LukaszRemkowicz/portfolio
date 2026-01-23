# backend/astrophotography/models.py
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from django_countries.fields import CountryField
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseImage

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


class Place(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("The name of the specific place or city."),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        ordering = ["name"]


class Telescope(models.Model):
    model = models.CharField(
        max_length=255,
        verbose_name=_("Model"),
        help_text=_("Telescope model and specifications"),
    )

    def __str__(self) -> str:
        return self.model

    class Meta:
        verbose_name = _("Telescope")
        verbose_name_plural = _("Telescopes")
        ordering = ["model"]


class Camera(models.Model):
    model = models.CharField(
        max_length=255,
        verbose_name=_("Model"),
        help_text=_("Camera model and specifications"),
    )

    def __str__(self) -> str:
        return self.model

    class Meta:
        verbose_name = _("Camera")
        verbose_name_plural = _("Cameras")
        ordering = ["model"]


class Lens(models.Model):
    model = models.CharField(
        max_length=255,
        verbose_name=_("Model"),
        help_text=_("Lens model and focal length"),
    )

    def __str__(self) -> str:
        return self.model

    class Meta:
        verbose_name = _("Lens")
        verbose_name_plural = _("Lenses")
        ordering = ["model"]


class Tracker(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Star tracker or mount model"),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Tracker")
        verbose_name_plural = _("Trackers")
        ordering = ["name"]


class Tripod(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Tripod model"),
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Tripod")
        verbose_name_plural = _("Tripods")
        ordering = ["name"]


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
        from django.utils.text import slugify

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
