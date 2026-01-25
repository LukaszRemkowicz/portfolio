from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

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

    def changelist_view(self, request, extra_context=None):
        """Redirect to the change page for the singleton instance."""
        obj = self.model.objects.last()
        if not obj:
            # If not seeded, let the standard view handle it or create one
            return super().changelist_view(request, extra_context)

        return redirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context.update(
            {
                "show_save_and_continue": False,
                "show_save_and_add_another": False,
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "contact_form_enabled",
                    "travel_highlights_enabled",
                    "programming_enabled",
                    "lastimages_enabled",
                    "meteors",
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
        "meteors",
    )
