from typing import Optional

from django.db import models

from core.models import BaseImage

# Create your models here.


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

    def __str__(self):
        return self.name


class ProjectImage(BaseImage):
    """Model for programming project images"""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    is_cover = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Project Image"
        verbose_name_plural = "Project Images"


class ProgrammingPageConfig(models.Model):
    """
    Configuration for the programming page.
    Singleton pattern: Only one configuration instance is allowed.
    """

    enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programming Page Configuration"
        verbose_name_plural = "Programming Page Configuration"

    def __str__(self) -> str:
        return f"Programming Page Config (Enabled: {self.enabled})"

    def save(self, *args: tuple, **kwargs: dict) -> None:
        """Enforce singleton pattern"""
        if not self.pk and ProgrammingPageConfig.objects.exists():
            return  # Prevent creation of multiple instances
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls) -> Optional["ProgrammingPageConfig"]:
        """Get the single configuration instance or create it if it doesn't exist"""
        config, _created = cls.objects.get_or_create(pk=1)
        return config
