from django.contrib import admin

from .models import LandingPageSettings


@admin.register(LandingPageSettings)
class LandingPageSettingsAdmin(admin.ModelAdmin):
    """Admin for the singleton LandingPageSettings model."""

    def has_add_permission(self, request):
        """Prevent creating more than one instance."""
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the settings."""
        return False

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "contact_form_enabled",
                    "travel_highlights_enabled",
                    "programming_enabled",
                    "lastimages_enabled",
                    "meteors_enabled",
                )
            },
        ),
    )
    list_display = (
        "__str__",
        "contact_form_enabled",
        "travel_highlights_enabled",
        "programming_enabled",
        "lastimages_enabled",
        "meteors_enabled",
    )
