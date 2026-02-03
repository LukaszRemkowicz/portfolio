# backend/programming/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from django_ckeditor_5.fields import CKEditor5Field

from core.models import BaseImage


class Project(models.Model):
    """Model for programming projects"""

    name = models.CharField(max_length=255)
    description = models.TextField()
    technologies = models.TextField()
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class ProjectImage(BaseImage):
    """Model for programming project images"""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    is_cover = models.BooleanField(default=False)

    translations = TranslatedFields(
        name=models.CharField(
            max_length=255, verbose_name=_("Name"), help_text=_("A descriptive name for this image.")
        ),
        description=CKEditor5Field(
            blank=True,
            verbose_name=_("Description"),
            help_text=_("Optional detailed description of the image."),
            config_name="default",
        )
    )

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"
