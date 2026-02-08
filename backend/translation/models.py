# backend/translation/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class TranslationTask(models.Model):
    """Tracks status of Celery translation tasks."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        RUNNING = "RUNNING", _("Running")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")

    task_id = models.CharField(max_length=255, unique=True, help_text=_("Celery Task ID"))

    # Generic Foreign Key to support both AstroImage (UUID) and Place/Tag (Int)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(
        max_length=255, help_text=_("Primary Key of the object (Int or UUID)")
    )
    content_object = GenericForeignKey("content_type", "object_id")

    language = models.CharField(max_length=10, verbose_name=_("Target Language"))
    method = models.CharField(max_length=100, verbose_name=_("Translation Method"))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Task Status"),
    )
    error_message = models.TextField(blank=True, null=True, verbose_name=_("Error Message"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Translation Task")
        verbose_name_plural = _("Translation Tasks")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.method} ({self.language}): {self.get_status_display()}"
