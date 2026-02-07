import logging

from parler.admin import TranslatableAdmin, TranslatableTabularInline

from django.conf import settings
from django.contrib import admin

from translation.services import TranslationService

from .models import Project, ProjectImage

logger = logging.getLogger(__name__)


class ProjectImageInline(TranslatableTabularInline):
    """Inline for managing project images with translation support."""

    model = ProjectImage
    extra = 1
    fields = ("name", "description", "path", "is_cover")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Admin configuration for Programming Projects.
    Projects currently use standard fields, with images managed via TranslatableTabularInline.
    """

    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description", "technologies")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "description", "technologies")}),
        ("Links", {"fields": ("github_url", "live_url")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")
    inlines = [ProjectImageInline]


@admin.register(ProjectImage)
class ProjectImageAdmin(TranslatableAdmin):
    """
    Admin configuration for Project Images.
    Supports automated translation of image metadata (name, description).
    """

    list_display = ("name", "project", "is_cover", "created_at")
    list_filter = ("is_cover", "project", "created_at")
    search_fields = ("name", "description", "project__name")
    ordering = ("project", "-is_cover", "-created_at")

    fieldsets = (
        (None, {"fields": ("project", "name", "description")}),
        ("Image", {"fields": ("path", "is_cover")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        """
        Saves the project image and triggers automated translations for metadata.
        """
        super().save_model(request, obj, form, change)
        supported_languages = TranslationService.get_available_languages()
        for lang_code in supported_languages:
            if lang_code == settings.PARLER_DEFAULT_LANGUAGE_CODE:
                continue
            logger.info(f"Triggering ProjectImage translations for '{obj.name}' into {lang_code}")
            # Generic parler translation trigger
            TranslationService._translate_parler_fields(obj, ["name", "description"], lang_code)
