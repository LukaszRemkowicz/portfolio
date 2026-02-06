# backend/users/admin.py
import logging

from parler.admin import TranslatableAdmin

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from translation.mixins import DynamicParlerStyleMixin, HideNonTranslatableFieldsMixin

from .models import Profile

User = get_user_model()
logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(
    DynamicParlerStyleMixin, HideNonTranslatableFieldsMixin, TranslatableAdmin, DjangoUserAdmin
):
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

    @property
    def change_form_template(self) -> str:
        """
        Force our robust template to ensure tabs are visible.
        This overrides TranslatableAdmin's dynamic property.
        """
        return "admin/users/user/robust_change_form.html"

    def get_change_form_base_template(self):
        """
        TranslatableAdmin uses this to determine what to extend.
        We force it to the standard admin template so our robust one doesn't circular loop.
        """
        return "admin/change_form.html"

    # Fields to show when editing a translation (used by HideNonTranslatableFieldsMixin)
    translatable_fields = ["short_description", "bio"]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """
        Ensure language_tabs are in context.
        """
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            available_languages = self.get_available_languages(obj)
            extra_context["language_tabs"] = self.get_language_tabs(
                request, obj, available_languages
            )

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """
        Manually enforce our robust template to bypass base class shadowing.
        """
        response = super().render_change_form(request, context, add, change, form_url, obj)

        from django.template.response import TemplateResponse

        if isinstance(response, TemplateResponse):
            response.template_name = self.change_form_template

        return response

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
