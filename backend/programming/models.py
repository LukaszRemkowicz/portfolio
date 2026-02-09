# backend/programming/models.py
from django_ckeditor_5.fields import CKEditor5Field
from parler.managers import TranslatableManager
from parler.models import TranslatedFields

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseImage
from translation.mixins import AutomatedTranslationModelMixin


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


class ProjectImage(AutomatedTranslationModelMixin, BaseImage):
    """Model for programming project images"""

    # Translation trigger fields
    translation_service_method = "translate_project_image"
    translation_trigger_fields = ["name", "description"]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    is_cover = models.BooleanField(default=False)

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
    )

    objects = TranslatableManager()

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"

    def clean(self):
        """Enforce that the name is required for the default language."""
        super().clean()
        default_lang = settings.DEFAULT_APP_LANGUAGE
        name = self.safe_translation_getter("name", language_code=default_lang)
        if not name:
            raise ValidationError({"name": _("This field is required for the default language.")})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.trigger_translations()

    def __str__(self) -> str:
        return self.safe_translation_getter("name", any_language=True) or f"Project Image {self.pk}"
