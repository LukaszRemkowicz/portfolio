# backend/core/models.py
import uuid
from io import BytesIO
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from PIL import Image

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseImage(models.Model):
    """Base abstract model for images"""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    path = models.ImageField(
        upload_to="images/",
        verbose_name=_("Image File"),
        help_text=_("The actual image file to be displayed."),
    )
    name = models.CharField(
        max_length=255, verbose_name=_("Name"), help_text=_("A descriptive name for this image.")
    )
    description = CKEditor5Field(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional detailed description of the image."),
        config_name="default",
    )
    thumbnail = models.ImageField(
        upload_to="thumbnails/", blank=True, null=True, editable=False, verbose_name=_("Thumbnail")
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.path and not self.thumbnail:
            self.thumbnail = self.make_thumbnail(self.path)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def make_thumbnail(self, image: Any, size: tuple[int, int] = (400, 400)) -> ContentFile:
        """Generates a thumbnail for the image."""
        img: Any = Image.open(image)
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
        thumbnail_name = f"thumb_{getattr(image, 'name', 'unknown').split('/')[-1]}"
        return ContentFile(thumb_io.getvalue(), name=thumbnail_name)


class SingletonModel(models.Model):
    """Abstract singleton model to ensure only one instance exists in the database."""

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.pk and type(self).objects.exists():  # type: ignore[attr-defined]
            # If creating a new one but instance already exists, stop or update existing.
            # Default behavior for settings: update fields of the existing instance.
            existing = type(self).objects.first()  # type: ignore[attr-defined]
            if existing:
                for field in self._meta.fields:
                    if field.name not in ["id", "pk"]:
                        setattr(existing, field.name, getattr(self, field.name))
                existing.save(*args, **kwargs)
                return
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> Any:
        """Load the singleton instance, creating it with defaults if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(pk=1)  # type: ignore[attr-defined]
        return obj


class LandingPageSettings(SingletonModel):
    """Singleton-like model to store global landing page settings."""

    contact_form_enabled = models.BooleanField(default=True, verbose_name=_("Contact Form Enabled"))
    travel_highlights_enabled = models.BooleanField(
        default=True, verbose_name=_("Travel Highlights Enabled")
    )
    programming_enabled = models.BooleanField(
        default=True, verbose_name=_("Programming Section Enabled")
    )
    lastimages_enabled = models.BooleanField(
        default=True, verbose_name=_("Last Images Section Enabled")
    )
    meteors_enabled = models.BooleanField(default=True, verbose_name=_("Meteors Enabled"))

    class Meta:
        verbose_name = _("Landing Page Settings")
        verbose_name_plural = _("Landing Page Settings")

    def __str__(self) -> str:
        return str(_("Landing Page Settings"))
