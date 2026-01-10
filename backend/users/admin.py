# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import UserLoginAttempts

User = get_user_model()


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
                    "bio",
                    "avatar",
                    "about_me_image",
                    "about_me_image2",
                )
            },
        ),
        (
            _("Social Media"),
            {
                "fields": (
                    "website",
                    "github_profile",
                    "linkedin_profile",
                    "astrobin_url",
                    "fb_url",
                    "ig_url",
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
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "created_at")
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
        """Redirect to edit form if user exists, otherwise allow add"""
        user = User.get_user()
        if user and user.pk:
            from django.shortcuts import redirect
            from django.urls import reverse

            return redirect(reverse("admin:users_user_change", args=[user.pk]))
        return super().changelist_view(request, extra_context)


@admin.register(UserLoginAttempts)
class UserLoginAttemptsAdmin(admin.ModelAdmin):
    """Admin interface for UserLoginAttempts model"""

    list_display = ("id", "attempted_at", "counter")
    list_display_links = ("id", "attempted_at")
    list_filter = ("attempted_at",)
    search_fields = ("id",)
    ordering = ("-attempted_at",)

    fieldsets = (
        (
            "Login Attempt Info",
            {
                "fields": (
                    "attempted_at",
                    "counter",
                )
            },
        ),
    )
