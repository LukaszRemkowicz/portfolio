import uuid

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
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional detailed description of the image."),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class LandingPageSettings(models.Model):
    """Singleton-like model to store global landing page settings."""

    contact_form_enabled = models.BooleanField(default=True, verbose_name=_("Contact Form Enabled"))
    location_slider_enabled = models.BooleanField(
        default=True, verbose_name=_("Location Slider Enabled")
    )
    programming_enabled = models.BooleanField(
        default=True, verbose_name=_("Programming Section Enabled")
    )

    class Meta:
        verbose_name = _("Landing Page Settings")
        verbose_name_plural = _("Landing Page Settings")

    def __str__(self):
        return str(_("Landing Page Settings"))

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        if not self.pk and LandingPageSettings.objects.exists():
            # If you try to create a new one, but one exists, update the existing one instead
            existing = LandingPageSettings.objects.first()
            existing.contact_form_enabled = self.contact_form_enabled
            existing.location_slider_enabled = self.location_slider_enabled
            existing.programming_enabled = self.programming_enabled
            return existing.save(*args, **kwargs)
        return super().save(*args, **kwargs)
