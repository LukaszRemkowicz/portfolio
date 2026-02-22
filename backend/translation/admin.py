# backend/translation/admin.py
import logging

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from .models import TranslationTask

logger = logging.getLogger(__name__)


@admin.register(TranslationTask)
class TranslationTaskAdmin(admin.ModelAdmin):
    """Admin for monitoring translation tasks."""

    list_display = ("task_id", "target_object", "language", "method", "status", "created_at")
    list_filter = ("status", "language", "method")
    search_fields = ("task_id", "error_message")
    readonly_fields = ("created_at", "updated_at")

    def target_object(self, obj: TranslationTask) -> str:
        """
        Safely attempts to render the target object's string representation.
        If the object is a Parler model that currently lacks translations,
        str() will raise DoesNotExist. We catch this and return a safe fallback.
        """
        target = obj.content_object
        if not target:
            return f"Deleted {obj.content_type.model} (ID: {obj.object_id})"
        try:
            return str(target)
        except ObjectDoesNotExist:
            return f"{obj.content_type.model} (ID: {obj.object_id} - Untranslated)"
        except Exception:
            logger.exception(
                "Unexpected error rendering target_object for TranslationTask pk=%s",
                obj.pk,
            )
            return f"{obj.content_type.model} (ID: {obj.object_id} - Error)"

    target_object.short_description = "Content Object"  # type: ignore[attr-defined]

    def has_add_permission(self, request):
        return False
