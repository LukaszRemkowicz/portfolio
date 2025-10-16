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
