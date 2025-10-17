from django.contrib import admin
from .models import AstroImage, BackgroundMainPage

@admin.register(AstroImage)
class AstroImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'celestial_object', 'capture_date', 'location', 'created_at')
    list_filter = ('capture_date', 'location', 'celestial_object', 'created_at')
    search_fields = ('name', 'description', 'celestial_object', 'location', 'equipment')
    date_hierarchy = 'capture_date'
    ordering = ('-capture_date', '-created_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'path')
        }),
        ('Capture Details', {
            'fields': (
                'capture_date',
                'location',
                'celestial_object',
                'equipment',
                'exposure_details',
            )
        }),
        ('Processing', {
            'fields': ('processing_details',)
        }),
        ('Links', {
            'fields': ('astrobin_url',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BackgroundMainPage)
class BackgroundMainPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'created_at')
    readonly_fields = ('created_at',)
