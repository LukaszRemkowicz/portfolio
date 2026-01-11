# backend/astrophotography/models.py
import uuid

from django.db import models

from core.models import BaseImage

CelestialObjectChoices = [
    ("Landscape", "Landscape"),
    ("Deep Sky", "Deep Sky"),
    ("Startrails", "Startrails"),
    ("Solar System", "Solar System"),
    ("Milky Way", "Milky Way"),
    ("Northern Lights", "Northern Lights"),
]


class AstroImage(BaseImage):
    """Model for astrophotography images"""

    capture_date = models.DateField()
    location = models.CharField(max_length=255)
    equipment = models.TextField(blank=True)
    exposure_details = models.TextField(blank=True)
    processing_details = models.TextField(blank=True)
    celestial_object = models.CharField(choices=CelestialObjectChoices)
    astrobin_url = models.URLField(
        max_length=200,
        blank=True,
        help_text=("Link to this image on Astrobin " "(e.g., https://www.astrobin.com/XXXXX/)"),
    )

    class Meta:
        verbose_name = "Astrophotography Image"
        verbose_name_plural = "Astrophotography Images"
        ordering = ["-created_at"]


class BackgroundMainPage(models.Model):
    """Model for the main page background image"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to="backgrounds/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BackgroundMainPage {self.pk}"
