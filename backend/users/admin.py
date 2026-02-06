# backend/users/admin.py
import logging
from typing import Any

from parler.admin import TranslatableAdmin

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from translation.mixins import (
    AutomatedTranslationMixin,
    DynamicParlerStyleMixin,
    HideNonTranslatableFieldsMixin,
    TranslationStatusMixin,
)

from .models import Profile

User = get_user_model()
logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(  # type: ignore[misc]
    AutomatedTranslationMixin,
    TranslationStatusMixin,
    DynamicParlerStyleMixin,
    HideNonTranslatableFieldsMixin,
    TranslatableAdmin,
    DjangoUserAdmin,
):
    """
    Define admin model for custom User model with email as username.
    Singleton pattern: Only one user is allowed.
    """

    translation_service_method = "translate_user"
    translation_trigger_fields = ["short_description", "bio"]

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
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Important dates"),
            {
                "fields": ("last_login", "date_joined", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @property  # type: ignore[override]
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

    def get_fieldsets(self, request: HttpRequest, obj: models.Model | None = None):
        """Dynamically add translation_status to Personal info on default language tab."""
        fieldsets = super().get_fieldsets(request, obj)
        if not obj:
            return fieldsets
        current_language = request.GET.get("language")
        default_language = getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", "en")
        if not current_language or current_language == default_language:
            fieldsets = list(fieldsets)
            for index, (name, opts) in enumerate(fieldsets):
                if name == _("Personal info"):
                    new_opts = opts.copy()
                    fields = list(new_opts["fields"])
                    fields.insert(0, "translation_status")
                    new_opts["fields"] = tuple(fields)
                    fieldsets[index] = (name, new_opts)
                    break
            return tuple(fieldsets)
        return fieldsets

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict[str, Any] | None = None,
    ):
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

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Any | None = None,
    ):
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
    readonly_fields = ("created_at", "updated_at", "translation_status")

    def has_add_permission(self, request) -> bool:
        """Only allow adding a user if no user exists (singleton pattern)"""
        return not User.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        """Prevent deletion of the user (singleton pattern)"""
        return False

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, Any] | None = None):
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
