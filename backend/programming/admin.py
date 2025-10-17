from django.contrib import admin

from .models import Project, ProjectImage


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("name", "description", "path", "is_cover")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
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
class ProjectImageAdmin(admin.ModelAdmin):
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
