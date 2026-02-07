import logging

from django.contrib import admin

from .models import ContactMessage

logger = logging.getLogger(__name__)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing contact form submissions.
    Automatically marks messages as read when viewed.
    """

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
        Overrides the change form view to automatically mark a message as read
        when it's opened for viewing in the admin.
        """
        if object_id:
            try:
                contact_message = ContactMessage.objects.get(id=object_id)
                if not contact_message.is_read:
                    logger.info(f"Marking ContactMessage {object_id} as read.")
                    contact_message.is_read = True
                    contact_message.save()
            except ContactMessage.DoesNotExist:
                # If the message was deleted while opening it, we simply ignore it since
                # we are only trying to mark it as read.
                pass

        return super().changeform_view(request, object_id, form_url, extra_context)
