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
