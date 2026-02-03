# backend/users/admin.py
import logging

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Profile

User = get_user_model()
logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Define admin model for custom User model with email as username.
    Singleton pattern: Only one user is allowed.
    """

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "short_description",
                    "bio",
                    "contact_email",
                    "avatar",
                    "about_me_image",
                    "about_me_image2",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "short_description",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_display_links = ("email",)
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request) -> bool:
        """Only allow adding a user if no user exists (singleton pattern)"""
        return not User.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prevent deletion of the user (singleton pattern)"""
        return False

    def changelist_view(self, request, extra_context=None):
        """
        Redirect to the change view if a user instance already exists.
        This provides a better UX for the singleton pattern by skipping the list view.
        """
        user = User.get_user()
        if user and user.pk:
            from django.shortcuts import redirect
            from django.urls import reverse

            return redirect(reverse("admin:users_user_change", args=[user.pk]))
        return super().changelist_view(request, extra_context)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing different user profiles"""

    list_display = ("type", "title", "is_active", "updated_at")
    list_filter = ("type", "is_active")
    search_fields = ("title", "specific_bio")

    fieldsets = (
        (None, {"fields": ("type", "user", "is_active")}),
        (
            "Content",
            {
                "fields": (
                    "title",
                    "specific_bio",
                )
            },
        ),
        (
            "Links",
            {
                "fields": (
                    "github_url",
                    "linkedin_url",
                    "astrobin_url",
                    "fb_url",
                    "ig_url",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request) -> bool:
        """Limit profiles to the defined types (Programming, Astro)"""
        return Profile.objects.count() < 2
