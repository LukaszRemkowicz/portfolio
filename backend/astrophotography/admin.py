from django.contrib import admin

from .forms import AstroImageForm
from .models import AstroImage, BackgroundMainPage


@admin.register(AstroImage)
class AstroImageAdmin(admin.ModelAdmin):
    form = AstroImageForm
    list_display = ("name", "capture_date", "celestial_object", "has_thumbnail", "tag_list")
    list_filter = ("celestial_object", "capture_date", "tags")
    search_fields = ("name", "description", "location", "equipment")

    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())

    date_hierarchy = "capture_date"
    ordering = ("-capture_date", "-created_at")

    @admin.display(boolean=True, description="Has Thumbnail")
    def has_thumbnail(self, obj):
        return bool(obj.thumbnail)

    fieldsets = (
        (None, {"fields": ("name", "description", "path", "tags")}),
        (
            "Capture Details",
            {
                "fields": (
                    "capture_date",
                    "location",
                    "celestial_object",
                    "equipment",
                    "exposure_details",
                )
            },
        ),
        ("Processing", {"fields": ("processing_details",)}),
        ("Links", {"fields": ("astrobin_url",)}),
        ("Thumbnail", {"fields": ("thumbnail",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at", "thumbnail")


@admin.register(BackgroundMainPage)
class BackgroundMainPageAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "created_at")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "description", "path")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
