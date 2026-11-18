from parler.admin import TranslatableAdmin, TranslatableTabularInline
from parler.forms import TranslatableModelForm

from django import forms
from django.contrib import admin

from .models import Project, ProjectImage


class ProjectImageAdminForm(TranslatableModelForm):
    original_upload = forms.ImageField(required=False, label="Original Image")

    class Meta:
        model = ProjectImage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_source = self.instance.original
        self.fields["original_upload"].required = not bool(current_source)

    def _post_clean(self) -> None:
        uploaded_original = self.cleaned_data.get("original_upload")
        if uploaded_original:
            self.instance.original = uploaded_original
        super()._post_clean()


class ProjectImageInline(TranslatableTabularInline):
    """Inline for managing project images with translation support."""

    model = ProjectImage
    form = ProjectImageAdminForm
    extra = 1
    fields = ("name", "description", "original_upload", "is_cover")


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

    form = ProjectImageAdminForm
    list_display = ("name", "project", "is_cover", "created_at")
    list_filter = ("is_cover", "project", "created_at")
    search_fields = ("name", "description", "project__name")
    ordering = ("project", "-is_cover", "-created_at")

    fieldsets = (
        (None, {"fields": ("project", "name", "description")}),
        ("Image", {"fields": ("original_upload", "is_cover")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")
