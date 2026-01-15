from django.contrib import admin

from .models import ProgrammingPageConfig, Project, ProjectImage


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


@admin.register(ProgrammingPageConfig)
class ProgrammingPageConfigAdmin(admin.ModelAdmin):
    """Admin for ProgrammingPageConfig with singleton pattern enforcement"""

    list_display = ("enabled", "updated_at")

    def has_add_permission(self, request) -> bool:
        """Only allow adding a config if none exists"""
        return not ProgrammingPageConfig.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prevent deletion of the configuration"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to edit form if config exists, otherwise allow add"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        config = ProgrammingPageConfig.get_config()
        if config and config.pk:
            return HttpResponseRedirect(
                reverse(
                    f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                    args=(config.pk,),
                )
            )
        return super().changelist_view(request, extra_context)
