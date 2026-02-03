# backend/core/models.py
import uuid
from io import BytesIO
from typing import Any

from django_ckeditor_5.fields import CKEditor5Field
from PIL import Image

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _


from parler.models import TranslatableModel, TranslatedFields

class BaseImage(TranslatableModel):
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
    
    # Translations moved to concrete subclasses because BaseImage is abstract.
    # See AstroImage and ProjectImage.

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
        name = self.safe_translation_getter("name", any_language=True)
        return name if name else str(self.id)

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

    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Prevent saving more than one instance."""
        if not self.pk and self.__class__.objects.exists():
            raise ValidationError(
                _("A singleton instance of %s already exists.") % self._meta.verbose_name
            )
        super().save(*args, **kwargs)
        # Cleanup: Delete all other instances except the one just saved
        self.__class__.objects.exclude(pk=self.pk).delete()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        """Prevent deletion of the singleton instance via standard delete."""
        return 0, {}


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
    meteors = models.ForeignKey(
        "astrophotography.MeteorsMainPageConfig",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Meteors Configuration"),
        help_text=_("Select the configuration to enable meteors. Leave empty to disable."),
    )

    class Meta:
        verbose_name = _("Landing Page Settings")
        verbose_name_plural = _("Landing Page Settings")

    def __str__(self) -> str:
        return str(_("Landing Page Settings"))
