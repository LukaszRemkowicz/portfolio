# backend/translation/admin.py
from django.contrib import admin

from .models import TranslationTask


@admin.register(TranslationTask)
class TranslationTaskAdmin(admin.ModelAdmin):
    """Admin for monitoring translation tasks."""

    list_display = ("task_id", "content_object", "language", "method", "status", "created_at")
    list_filter = ("status", "language", "method")
    search_fields = ("task_id", "error_message")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        return False
