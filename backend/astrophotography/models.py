from io import BytesIO

from PIL import Image
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseImage

CelestialObjectChoices = [
    ("Landscape", "Landscape"),
    ("Deep Sky", "Deep Sky"),
    ("Startrails", "Startrails"),
    ("Solar System", "Solar System"),
    ("Milky Way", "Milky Way"),
    ("Northern Lights", "Northern Lights"),
]


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


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
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True, editable=False)
    tags = TaggableManager(through=UUIDTaggedItem)

    def save(self, *args, **kwargs):
        if self.path and not self.thumbnail:
            self.thumbnail = self.make_thumbnail(self.path, size=(400, 400))
        super().save(*args, **kwargs)

    def make_thumbnail(self, image, size=(400, 400)):
        """Generates a thumbnail for the image."""
        img = Image.open(image)
        # Handle transparency: create a white background if image has alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")

        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, "JPEG", quality=85)

        thumbnail_name = f"thumb_{image.name.split('/')[-1]}"
        return ContentFile(thumb_io.getvalue(), name=thumbnail_name)

    class Meta:
        verbose_name = "Astrophotography Image"
        verbose_name_plural = "Astrophotography Images"
        ordering = ["-created_at"]


class BackgroundMainPage(BaseImage):
    """Model for the main page background image"""

    # Override fields with appropriate defaults
    name = models.CharField(max_length=255, default="Background Image")
    path = models.ImageField(upload_to="backgrounds/")

    class Meta:
        verbose_name = "Background Main Page"
        verbose_name_plural = "Background Main Pages"
        ordering = ["-created_at"]
