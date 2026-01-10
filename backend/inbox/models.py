import logging

from django.db import models

logger = logging.getLogger(__name__)


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.name} - {self.subject} " f"({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ContactFormSettings(models.Model):
    """
    Singleton model for contact form settings (kill switch).
    Only one instance should exist - use get_or_create(pk=1) to access.
    """

    enabled = models.BooleanField(
        default=False,
        help_text="Enable or disable the contact form endpoint. "
        "When disabled, all submissions will be rejected.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contact Form Settings"
        verbose_name_plural = "Contact Form Settings"

    def __str__(self) -> str:
        return f"Contact Form Settings (Enabled: {self.enabled})"

    @classmethod
    def get_settings(cls) -> "ContactFormSettings":
        """Get the singleton settings instance, creating if it doesn't exist"""
        settings, _ = cls.objects.get_or_create(pk=1, defaults={"enabled": False})
        return settings

    def save(self, *args: tuple, **kwargs: dict) -> None:
        """
        Override save to ensure only one instance exists.
        Handles potential failures during save() due to singleton pattern constraints.
        """
        from django.db import IntegrityError
        from django.utils import timezone

        self.pk = 1

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            # Handle race condition or constraint violation during save
            # Try to update existing instance using update() to avoid save() recursion
            try:
                type(self).objects.filter(pk=1).update(
                    enabled=self.enabled,
                    updated_at=timezone.now(),
                )
            except Exception as update_error:
                logger.error(f"Failed to update ContactFormSettings: {update_error}")
                raise
        except Exception as error:
            # Log unexpected errors and re-raise
            logger.error(f"Failed to save ContactFormSettings: {error}")
            raise
