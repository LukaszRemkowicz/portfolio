from django.contrib import admin

from .models import ContactFormSettings, ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "created_at", "is_read"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["name", "email", "subject", "message"]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["is_read"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Contact Information", {"fields": ("name", "email", "subject")}),
        ("Message", {"fields": ("message",)}),
        ("Status", {"fields": ("is_read",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """
        Override to automatically mark message as read when viewed
        """
        if object_id:
            try:
                contact_message = ContactMessage.objects.get(id=object_id)
                if not contact_message.is_read:
                    contact_message.is_read = True
                    contact_message.save()
            except ContactMessage.DoesNotExist:
                # If the message was deleted while opening it, we simply ignore it since
                # we are only trying to mark it as read.
                pass

        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(ContactFormSettings)
class ContactFormSettingsAdmin(admin.ModelAdmin):
    """Admin for contact form settings (singleton model)"""

    list_display = ["enabled", "updated_at"]
    readonly_fields = ["updated_at"]
    fieldsets = (
        (
            "Contact Form Control",
            {
                "fields": ("enabled",),
                "description": "Use this as a kill switch to disable the contact form endpoint. "
                "When disabled, submissions will be rejected immediately with HTTP 503.",
            },
        ),
        ("Timestamps", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request) -> bool:
        """Only allow one instance"""
        return not ContactFormSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prevent deletion of settings"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to edit form if singleton exists, otherwise allow add"""
        settings = ContactFormSettings.get_settings()
        if settings.pk:
            from django.shortcuts import redirect
            from django.urls import reverse

            return redirect(reverse("admin:inbox_contactformsettings_change", args=[settings.pk]))
        return super().changelist_view(request, extra_context)
